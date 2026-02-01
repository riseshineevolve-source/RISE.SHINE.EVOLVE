export default {
  async fetch(request, env) {
    // 1. Obsługa CORS (dla strony www)
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    const url = new URL(request.url);

    // --- SCENARIUSZ A: UŻYTKOWNIK KLIKA W LINK W MAILU (GET) ---
    // Link wygląda tak: worker.url/confirm-delete?token=...&email=...&id=...
    if (request.method === "GET" && url.pathname === "/confirm-delete") {
      return await handleConfirmationLink(url, env);
    }

    // --- SCENARIUSZ B: AKCJE Z FORMULARZA NA STRONIE (POST) ---
    if (request.method === "POST") {
      const contentType = request.headers.get("content-type") || "";
      try {
        if (contentType.includes("application/json")) {
          const body = await request.json();
          
          // 1. Prośba o usunięcie (Wysyłamy maila z linkiem)
          if (body.type === 'request_delete') {
              return await sendDeleteConfirmationEmail(body, env, url.origin);
          }

          if (body.type === 'request_password_reset') {
              return await sendPasswordResetEmail(body, env);
          }

          // 2. Standardowy zapis (Welcome) - stary kod
          if (body.email && !body.type) {
               return await handleSubscription(body, env);
          }

          // 3. Sprawdzanie statusu (Bramkarz) - stary kod
          if (body.type === 'check_status') {
               return await checkSubscriptionStatus(body, env);
          }
        } else {
          const formData = await request.formData();
          const email = (formData.get("email") || formData.get("EMAIL") || "").toString().trim().toLowerCase();
          const firstName = (formData.get("firstName") || formData.get("FIRSTNAME") || "").toString().trim();
          const listId = formData.get("brevoListId") || env.BREVO_LIST_ID || 3;
          if (!email) {
            return new Response(JSON.stringify({ error: "Missing email" }), { status: 400 });
          }
          return await handleSubscription({ email, firstName, listId }, env);
        }
      } catch (error) {
        return new Response(JSON.stringify({ error: error.message }), { status: 500 });
      }
    }

    return new Response("Not found", { status: 404 });
  },
};

// --- FUNKCJE POMOCNICZE ---

// 1. Wysyłanie maila z podpisanym linkiem
async function sendDeleteConfirmationEmail(body, env, workerOrigin) {
    const { email } = body;
    let { userId } = body;
    if (!userId && email) {
        userId = await lookupSupabaseUserId(email, env);
    }
    if (!userId) {
        return new Response(JSON.stringify({ error: "Email not found in database", code: "email_not_found" }), {
            status: 404,
            headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
        });
    }

    // Generujemy podpis (HMAC)
    const dataToSign = `${email}:${userId}`;
    const signature = await generateHMAC(dataToSign, env.UNSUBSCRIBE_CONFIRM_SECRET);
    
    // Tworzymy link potwierdzający
    // Link kieruje z powrotem do tego Workera, ale na ścieżkę /confirm-delete
    const confirmLink = `${workerOrigin}/confirm-delete?email=${encodeURIComponent(email)}&userId=${encodeURIComponent(userId)}&sig=${signature}`;

    // Wysyłamy maila transakcyjnego przez Brevo
    const brevoResponse = await fetch("https://api.brevo.com/v3/smtp/email", {
        method: "POST",
        headers: {
            "api-key": env.BREVO_API_KEY,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            sender: { name: "Rise.Shine.Evolve", email: "hello@rise-shine-evolve-learning-hub.com" },
            to: [{ email: email }],
            templateId: 18,
            params: {
                CONFIRM_URL: confirmLink // To wstrzykujemy do przycisku w szablonie
            }
        })
    });

    if (!brevoResponse.ok) throw new Error("Błąd wysyłki maila Brevo");

    return new Response(JSON.stringify({ success: true, message: "Email wysłany" }), {
        headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
    });
}

// 1b. Wysyłanie maila resetującego hasło (template 19)
async function sendPasswordResetEmail(body, env) {
    const { email } = body;
    const templateId = Number(body.templateId || env.BREVO_PASSWORD_RESET_TEMPLATE_ID || 19);

    if (!email) {
        return new Response(JSON.stringify({ error: "Missing email" }), {
            status: 400,
            headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
        });
    }
    if (!env.SUPABASE_SERVICE_ROLE_KEY) {
        return new Response(JSON.stringify({ error: "Missing Supabase service role key" }), {
            status: 500,
            headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
        });
    }
    if (!env.BREVO_API_KEY) {
        return new Response(JSON.stringify({ error: "Missing Brevo API key" }), {
            status: 500,
            headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
        });
    }

    const supabaseResp = await fetch(`https://gegaodrfqwhrfdqtiokb.supabase.co/auth/v1/admin/users?email=${encodeURIComponent(email)}`, {
        method: "GET",
        headers: {
            "apikey": env.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
            "Content-Type": "application/json"
        }
    });

    if (!supabaseResp.ok) {
        return new Response(JSON.stringify({ error: "Unable to verify email", detail: await supabaseResp.text() }), {
            status: 500,
            headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
        });
    }

    const supabaseData = await supabaseResp.json().catch(() => ({}));
    const users = Array.isArray(supabaseData)
        ? supabaseData
        : (Array.isArray(supabaseData?.users) ? supabaseData.users : []);
    if (users.length === 0) {
        return new Response(JSON.stringify({ error: "Email not found", code: "email_not_found" }), {
            status: 404,
            headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
        });
    }

    const recoveryResult = await generateRecoveryLink(email, env);
    if (!recoveryResult?.link) {
        if (recoveryResult?.status === 400 || recoveryResult?.status === 404) {
            return new Response(JSON.stringify({ error: "Email not found", code: "email_not_found" }), {
                status: 404,
                headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
            });
        }
        return new Response(JSON.stringify({ error: "Unable to generate recovery link" }), {
            status: 500,
            headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
        });
    }

    const brevoResponse = await fetch("https://api.brevo.com/v3/smtp/email", {
        method: "POST",
        headers: {
            "api-key": env.BREVO_API_KEY,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            to: [{ email }],
            templateId,
            params: {
                RECOVERY_LINK: recoveryResult.link
            }
        })
    });

    if (!brevoResponse.ok) {
        return new Response(JSON.stringify({ error: "Brevo email send failed", detail: await brevoResponse.text() }), {
            status: 500,
            headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
        });
    }

    return new Response(JSON.stringify({ success: true, message: "Email sent" }), {
        headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" }
    });
}

async function generateRecoveryLink(email, env) {
    if (!env.SUPABASE_SERVICE_ROLE_KEY) {
        return null;
    }
    const redirectTo = env.SUPABASE_PASSWORD_RESET_REDIRECT || '';
    const payload = {
        type: "recovery",
        email
    };
    if (redirectTo) {
        payload.redirectTo = redirectTo;
    }
    const response = await fetch("https://gegaodrfqwhrfdqtiokb.supabase.co/auth/v1/admin/generate_link", {
        method: "POST",
        headers: {
            "apikey": env.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        return { link: null, status: response.status, error: await response.text() };
    }
    const data = await response.json().catch(() => ({}));
    const link = data?.action_link || data?.properties?.action_link || null;
    return { link, status: response.status };
}

// 2. Kliknięcie w link (Weryfikacja i usuwanie)
async function handleConfirmationLink(url, env) {
    const email = url.searchParams.get("email");
    const userId = url.searchParams.get("userId");
    const signature = url.searchParams.get("sig");

    if (!email || !userId || !signature) return new Response("Błędny link", { status: 400 });
    if (!env.UNSUBSCRIBE_CONFIRM_SECRET) {
        return new Response("Missing confirmation secret", { status: 500 });
    }
    if (!env.BREVO_API_KEY || !env.SUPABASE_SERVICE_ROLE_KEY) {
        return new Response("Missing service configuration", { status: 500 });
    }

    // Weryfikujemy podpis
    const dataToSign = `${email}:${userId}`;
    const expectedSignature = await generateHMAC(dataToSign, env.UNSUBSCRIBE_CONFIRM_SECRET);

    if (signature !== expectedSignature) {
        return new Response("Link jest nieprawidłowy lub sfałszowany!", { status: 403 });
    }

    // --- PODPIS PRAWIDŁOWY -> USUWANIE ---
    
    // A. Usuń z Brevo
    await fetch(`https://api.brevo.com/v3/contacts/${encodeURIComponent(email)}`, {
          method: "DELETE",
          headers: { "api-key": env.BREVO_API_KEY }
    });

    // B. Usuń z Supabase (Admin API)
    const supabaseResponse = await fetch(`https://gegaodrfqwhrfdqtiokb.supabase.co/auth/v1/admin/users/${userId}`, {
        method: "DELETE",
        headers: {
            "apikey": env.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
            "Content-Type": "application/json"
        }
    });

    if (!supabaseResponse.ok) return new Response("Błąd usuwania z bazy", { status: 500 });

    // C. Wyświetl prostą stronę potwierdzenia
    return new Response(`
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: green;">Your account has been successfully deleted.</h1>
                <p>We are sorry to see you go!</p>
                <p>Whenever you’re ready to return, we’ll be here - to Rise. Shine. Evolve.</p>
            </body>
        </html>
    `, { headers: { "Content-Type": "text/html; charset=utf-8" } });
}

// 3. Generowanie HMAC (Kryptografia)
async function generateHMAC(message, secret) {
    const encoder = new TextEncoder();
    const keyData = encoder.encode(secret);
    const key = await crypto.subtle.importKey("raw", keyData, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(message));
    
    // Konwersja na hex string
    return Array.from(new Uint8Array(signature)).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function lookupSupabaseUserId(email, env) {
    if (!env.SUPABASE_SERVICE_ROLE_KEY) {
        return '';
    }
    const response = await fetch(`https://gegaodrfqwhrfdqtiokb.supabase.co/auth/v1/admin/users?email=${encodeURIComponent(email)}`, {
        method: "GET",
        headers: {
            "apikey": env.SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": `Bearer ${env.SUPABASE_SERVICE_ROLE_KEY}`,
            "Content-Type": "application/json"
        }
    });
    if (!response.ok) {
        return '';
    }
    const data = await response.json().catch(() => ({}));
    const users = Array.isArray(data) ? data : (Array.isArray(data?.users) ? data.users : []);
    if (!users.length) {
        return '';
    }
    return users[0]?.id || '';
}

// 4. Stare funkcje (Zapis i Status - skrócone dla czytelności, wklej tu swoje pełne wersje jeśli modyfikowałaś)
async function handleSubscription(body, env) {
    // ... Twój kod zapisu do Brevo ...
      const updateResponse = await fetch("https://api.brevo.com/v3/contacts", {
        method: "POST",
        headers: { "Content-Type": "application/json", "api-key": env.BREVO_API_KEY },
        body: JSON.stringify({
          email: body.email,
          listIds: [Number(body.listId || 3)], 
          emailBlacklisted: false,
          updateEnabled: true,
          attributes: body.firstName ? { FIRSTNAME: body.firstName } : undefined
        })
      });
      return new Response(JSON.stringify({ success: updateResponse.ok }), { headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" } });
}

async function checkSubscriptionStatus(body, env) {
    // ... Twój kod sprawdzania (Bramkarz) ...
    // (Skopiuj logikę z poprzedniej odpowiedzi o "Bramkarzu")
     const checkUrl = `https://api.brevo.com/v3/contacts/${encodeURIComponent(body.email)}`;
        const response = await fetch(checkUrl, {
          method: "GET",
          headers: { "api-key": env.BREVO_API_KEY, "Content-Type": "application/json" }
        });
        if (!response.ok) return new Response(JSON.stringify({ active: false }), { headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" } });
        const data = await response.json();
        const isOnList = data.listIds && data.listIds.includes(3);
        const isNotBlocked = !data.emailBlacklisted;
        return new Response(JSON.stringify({ active: isOnList && isNotBlocked }), { headers: { "Access-Control-Allow-Origin": "*", "Content-Type": "application/json" } });
}
