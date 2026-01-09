// Cloudflare Worker: forwards form submissions to the site and (optionally) Brevo.
// How to wire Brevo so contacts land in your "RiseShineEvolve Subscribe" list:
//   1) In Brevo, open Contacts > Lists, click your list, and copy the numeric id from the URL.
//      For https://app.brevo.com/contact/list-listing/id/3 the numeric id is **3**.
//   2) In Cloudflare Workers > Settings > Variables, add:
//        - BREVO_API_KEY: your Brevo API key (keep it secret)
//        - BREVO_LIST_ID: 3  (the numeric id from step 1)
//        - SUPABASE_URL: your Supabase project URL
//          (legacy SUPABASE_URI is still accepted if already configured)
//        - SUPABASE_ANON_KEY: your Supabase anon key (for signup/login)
//        - SUPABASE_SERVICE_ROLE_KEY: your Supabase service role key (for account deletes)
//        - BREVO_UNSUBSCRIBE_TEMPLATE_ID: template id for unsubscribe follow-up email (optional)
//   3) Deploy the worker, then set CLOUDFLARE_WORKER_ENDPOINT in index.html to this worker's URL
//      (e.g., https://newsletter-endpoint.rise-shine-evolve.workers.dev/).
// The worker will forward to the site handler and also push to Brevo when both env vars are set.
export default {
  async fetch(request, env) {
    const sitePostTarget = 'https://rise-shine-evolve-learning-hub.com/';
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };
    const jsonResponse = (payload, status = 200) =>
      new Response(JSON.stringify(payload), {
        status,
        headers: { 'content-type': 'application/json', ...corsHeaders },
      });

    const supabaseUrl = (env.SUPABASE_URL || env.SUPABASE_URI || '')
      .toString()
      .trim()
      .replace(/\/$/, '');
    const supabaseAnonKey = (env.SUPABASE_ANON_KEY || '').toString().trim();
    const supabaseServiceKey = (env.SUPABASE_SERVICE_ROLE_KEY || '').toString().trim();

    const supabaseHeaders = (key) => ({
      apikey: key,
      Authorization: `Bearer ${key}`,
      'Content-Type': 'application/json',
    });

    const brevoHeaders = {
      'api-key': env.BREVO_API_KEY || '',
      'content-type': 'application/json',
      accept: 'application/json',
    };

    const requireBrevoKey = () => {
      if (!env.BREVO_API_KEY) {
        throw new Error('Missing Brevo API key');
      }
    };

    const requireSupabaseAnon = () => {
      if (!supabaseUrl || !supabaseAnonKey) {
        throw new Error('Missing Supabase configuration');
      }
    };

    const requireSupabaseService = () => {
      if (!supabaseUrl || !supabaseServiceKey) {
        throw new Error('Missing Supabase admin configuration');
      }
    };

    const resolveListId = (listId) => {
      const numericListId = Number(listId || env.BREVO_LIST_ID || '');
      if (!Number.isFinite(numericListId) || numericListId <= 0) {
        throw new Error('Missing or invalid Brevo list id');
      }
      return numericListId;
    };

    const upsertBrevoContact = async ({ email, firstName, listId }) => {
      requireBrevoKey();
      const numericListId = resolveListId(listId);

      const response = await fetch('https://api.brevo.com/v3/contacts', {
        method: 'POST',
        headers: brevoHeaders,
        body: JSON.stringify({
          email,
          attributes: firstName ? { FIRSTNAME: firstName } : {},
          updateEnabled: true,
          listIds: [numericListId],
        }),
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Brevo rejected the request');
      }
      return response.status;
    };

    const checkBrevoContact = async ({ email, listId }) => {
      requireBrevoKey();
      const numericListId = Number(listId || env.BREVO_LIST_ID || '');
      const contactEndpoint = `https://api.brevo.com/v3/contacts/${encodeURIComponent(email)}`;
      const brevoResp = await fetch(contactEndpoint, {
        method: 'GET',
        headers: {
          'api-key': env.BREVO_API_KEY,
          accept: 'application/json',
        },
      });

      const bodyText = await brevoResp.text();
      if (brevoResp.status === 404) {
        return { subscribed: false, listMatch: false, exists: false };
      }
      if (!brevoResp.ok) {
        throw new Error(bodyText || 'Brevo lookup failed');
      }

      let parsed = null;
      try {
        parsed = JSON.parse(bodyText);
      } catch (error) {
        parsed = null;
      }

      const listIds = Array.isArray(parsed?.listIds) ? parsed.listIds : [];
      const listMatch = numericListId ? listIds.includes(numericListId) : listIds.length > 0;
      const notBlacklisted = parsed ? parsed.emailBlacklisted === false : false;
      const subscribed = listMatch && notBlacklisted;

      return { subscribed, listMatch, exists: true };
    };

    const deleteBrevoContact = async (email, keepTransactional = true) => {
      requireBrevoKey();
      if (keepTransactional) {
        const response = await fetch(`https://api.brevo.com/v3/contacts/${encodeURIComponent(email)}`, {
          method: 'PUT',
          headers: {
            'api-key': env.BREVO_API_KEY,
            'content-type': 'application/json',
            accept: 'application/json',
          },
          body: JSON.stringify({
            email,
            listIds: [],
            emailBlacklisted: true,
            updateEnabled: true,
          }),
        });
        if (!response.ok && response.status !== 404) {
          const errorText = await response.text();
          throw new Error(errorText || 'Brevo unsubscribe failed');
        }
        return response.status;
      }
      const response = await fetch(`https://api.brevo.com/v3/contacts/${encodeURIComponent(email)}`, {
        method: 'DELETE',
        headers: {
          'api-key': env.BREVO_API_KEY,
          accept: 'application/json',
        },
      });
      if (!response.ok && response.status !== 404) {
        const errorText = await response.text();
        throw new Error(errorText || 'Brevo delete failed');
      }
      return response.status;
    };

    const supabaseSignUp = async ({ email, password, firstName }) => {
      requireSupabaseAnon();
      const response = await fetch(`${supabaseUrl}/auth/v1/signup`, {
        method: 'POST',
        headers: supabaseHeaders(supabaseAnonKey),
        body: JSON.stringify({
          email,
          password,
          data: firstName ? { first_name: firstName } : {},
        }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.error_description || data?.msg || 'Supabase signup failed');
      }
      return data;
    };

    const supabaseLogin = async ({ email, password }) => {
      requireSupabaseAnon();
      const response = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=password`, {
        method: 'POST',
        headers: supabaseHeaders(supabaseAnonKey),
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.error_description || data?.msg || 'Supabase login failed');
      }
      return data;
    };

    const supabaseDeleteUserByEmail = async (email) => {
      requireSupabaseService();
      const listResp = await fetch(`${supabaseUrl}/auth/v1/admin/users?email=${encodeURIComponent(email)}`, {
        method: 'GET',
        headers: supabaseHeaders(supabaseServiceKey),
      });
      const listData = await listResp.json().catch(() => ({}));
      if (!listResp.ok) {
        throw new Error(listData?.error_description || 'Supabase lookup failed');
      }

      const users = Array.isArray(listData?.users) ? listData.users : Array.isArray(listData) ? listData : [];
      const user = users[0];
      if (!user?.id) {
        return { deleted: false };
      }

      const deleteResp = await fetch(`${supabaseUrl}/auth/v1/admin/users/${user.id}`, {
        method: 'DELETE',
        headers: supabaseHeaders(supabaseServiceKey),
      });
      if (!deleteResp.ok) {
        const errorText = await deleteResp.text();
        throw new Error(errorText || 'Supabase delete failed');
      }
      return { deleted: true };
    };

    const sendBrevoUnsubscribeEmail = async ({ email }) => {
      requireBrevoKey();
      const senderEmail = (env.BREVO_SENDER_EMAIL || '').toString().trim();
      const senderName = (env.BREVO_SENDER_NAME || 'Rise.Shine.Evolve').toString().trim();
      const templateId = Number(env.BREVO_UNSUBSCRIBE_TEMPLATE_ID || '');
      const useTemplate = Number.isFinite(templateId) && templateId > 0;
      if (!useTemplate && !senderEmail) {
        return { sent: false, skipped: true, reason: 'Missing sender email' };
      }
      const htmlContent = `<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml">
<head>
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black" />
  <meta name="format-detection" content="telephone=no" />
  <title>Brevo</title>
  <link href="http://fonts.googleapis.com/css?family=Open+Sans:400,400,600,700,800,400italic" rel="stylesheet" type="text/css" />
  <style type="text/css">
    *{-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;}
    body{font-family:helvetica,arial,sans-serif;}
    table{margin:0 auto;}
    div,a,li,td{-webkit-text-size-adjust:none;}
    @media screen{body{font-family:"open sans",helvetica,arial,sans-serif;}}
    @media only screen and (max-width:640px){table[class=full]{width:100%!important;}}
    @media only screen and (max-width:479px){table[class=fullcenter]{width:100%!important;text-align:center!important;}}
  </style>
</head>
<body style="margin:0;padding:0;">
<table width="100%" cellspacing="0" cellpadding="0" border="0" align="center" bgcolor="#ffffff" style="background:#ffffff;">
  <tbody>
  <tr>
    <td>
      <table class="full" align="center" width="570" border="0" cellpadding="0" cellspacing="0" style="padding:0 5px;">
        <tbody>
        <tr>
          <td height="30" width="100%"></td>
        </tr>
        <!---------------------- begin Content -------------------->
        <!-- Title -->
        <tr>
          <td align="center" style="padding:0 20px;text-align:center;font-size:20px;color:#676a6c;line-height:30px;font-weight:600;" valign="middle" width="100%">
            We are sorry to see you go
          </td>
        </tr>
        <!-- /Title -->
        <tr>
          <td height="30" width="100%"></td>
        </tr>
        <!-- Text -->
        <tr>
          <td align="center" style="padding:0 20px;text-align:center;font-size:14px;color:#676a6c;line-height:24px;" valign="middle" width="100%">
         You’ve been unsubscribed.

 We believe in choosing what supports your growth.

 Whenever you feel ready: Rise.Shine.Evolve with us again.

      The Happy-Makers

          </td>
        </tr>
        <!-- /Text -->
        <tr>
          <td height="30" width="100%"></td>
        </tr>
        <!---------------------- end Content ---------------------->
        <tr>
          <td height="40" width="100%"></td>
        </tr>
        <tr>
          <td align="center" style="padding:0 20px;text-align:center;font-size:16px;color:#aaaaaa;line-height:30px;font-weight:700;" valign="middle" width="100%">
            Rise.Shine.Evolve.Learning.Hub.
          </td>
        </tr>
        <tr>
          <td height="40" width="100%"></td>
        </tr>
        </tbody>
      </table>
    </td>
  </tr>
  </tbody>
</table>
</body>
</html>`;
      const payload = useTemplate
        ? {
            to: [{ email }],
            templateId,
          }
        : {
            sender: { email: senderEmail, name: senderName },
            to: [{ email }],
            subject: 'We are sorry to see you go',
            htmlContent,
          };
      const response = await fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: {
          'api-key': env.BREVO_API_KEY,
          'content-type': 'application/json',
          accept: 'application/json',
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Brevo unsubscribe email failed');
      }
      return { sent: true };
    };

    if (request.method === 'OPTIONS') {
      return new Response('ok', { headers: corsHeaders });
    }

    if (request.method !== 'POST') {
      return new Response('ready', { headers: corsHeaders });
    }

    const contentType = request.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      let payload;
      try {
        payload = await request.json();
      } catch (error) {
        return new Response(JSON.stringify({ ok: false, error: 'Invalid JSON payload' }), {
          status: 400,
          headers: { 'content-type': 'application/json', ...corsHeaders },
        });
      }

      const email = (payload?.email || '').toString().trim();
      const lang = (payload?.lang || 'EN').toString().trim().toUpperCase() || 'EN';

      if (!email) {
        return new Response(JSON.stringify({ ok: false, error: 'Missing email' }), {
          status: 400,
          headers: { 'content-type': 'application/json', ...corsHeaders },
        });
      }

      if (!env.BREVO_API_KEY) {
        return new Response(JSON.stringify({ ok: false, error: 'Missing Brevo API key' }), {
          status: 400,
          headers: { 'content-type': 'application/json', ...corsHeaders },
        });
      }

      const brevoResponse = await fetch('https://api.brevo.com/v3/contacts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api-key': env.BREVO_API_KEY,
        },
        body: JSON.stringify({
          email,
          attributes: {
            LANG: lang,
          },
          updateEnabled: true,
        }),
      });

      if (brevoResponse.ok) {
        return new Response(JSON.stringify({ ok: true }), {
          headers: { 'content-type': 'application/json', ...corsHeaders },
        });
      }

      const errorText = await brevoResponse.text();
      return new Response(JSON.stringify({ ok: false, error: errorText }), {
        status: 400,
        headers: { 'content-type': 'application/json', ...corsHeaders },
      });
    }

    let formData;
    try {
      formData = await request.formData();
    } catch (error) {
      return jsonResponse({ ok: false, error: 'Invalid form data', detail: String(error) }, 400);
    }

    const action = (formData.get('action') || '').toString().trim();
    const firstName = (
      formData.get('firstName') ||
      formData.get('FIRSTNAME') ||
      ''
    ).toString().trim();
    const email = (formData.get('email') || formData.get('EMAIL') || '').toString().trim();
    const listId = formData.get('brevoListId') || env.BREVO_LIST_ID;

    // Quick Brevo contact check flow (no site forwarding)
    if (action === 'check') {
      if (!env.BREVO_API_KEY) {
        return new Response(JSON.stringify({ ok: false, error: 'Missing Brevo API key' }), {
          status: 400,
          headers: { 'content-type': 'application/json', ...corsHeaders },
        });
      }

      if (!email) {
        return new Response(JSON.stringify({ ok: false, error: 'Missing email' }), {
          status: 400,
          headers: { 'content-type': 'application/json', ...corsHeaders },
        });
      }

      const numericListId = Number(listId || '');
      const contactEndpoint = `https://api.brevo.com/v3/contacts/${encodeURIComponent(email)}`;
      const brevoResp = await fetch(contactEndpoint, {
        method: 'GET',
        headers: {
          'api-key': env.BREVO_API_KEY,
          accept: 'application/json',
        },
      });

      const bodyText = await brevoResp.text();
      if (!brevoResp.ok) {
        return new Response(
          JSON.stringify({ ok: false, brevoStatus: brevoResp.status, brevoBody: bodyText || null }),
          { headers: { 'content-type': 'application/json', ...corsHeaders }, status: brevoResp.status }
        );
      }

      let parsed = null;
      try {
        parsed = JSON.parse(bodyText);
      } catch (error) {
        // leave parsed null
      }

      const listIds = Array.isArray(parsed?.listIds) ? parsed.listIds : [];
      const listMatch = numericListId ? listIds.includes(numericListId) : listIds.length > 0;
      const notBlacklisted = parsed ? parsed.emailBlacklisted === false : false;
      const subscribed = listMatch && notBlacklisted;

      return new Response(
        JSON.stringify({
          ok: true,
          brevoStatus: brevoResp.status,
          brevoBody: parsed || bodyText || null,
          subscribed,
          listMatch,
        }),
        { headers: { 'content-type': 'application/json', ...corsHeaders } }
      );
    }

    if (action === 'unsubscribe') {
      if (!email) {
        return jsonResponse({ ok: false, error: 'Missing email' }, 400);
      }

      let brevoFound = false;
      let brevoRemoved = false;
      let supabaseFound = false;
      let supabaseRemoved = false;
      let brevoError = null;
      let supabaseError = null;

      try {
        requireBrevoKey();
      } catch (error) {
        brevoError = error?.message || 'Missing Brevo configuration';
      }

      try {
        requireSupabaseService();
      } catch (error) {
        supabaseError = error?.message || 'Missing Supabase configuration';
      }

      if (brevoError && supabaseError) {
        return jsonResponse(
          {
            ok: false,
            error: 'Missing configuration for unsubscribe.',
            brevoError,
            supabaseError,
          },
          400
        );
      }

      if (!brevoError) {
        try {
          const brevoStatus = await checkBrevoContact({ email, listId });
          brevoFound = Boolean(brevoStatus?.exists);
          if (brevoFound) {
            await deleteBrevoContact(email, true);
            brevoRemoved = true;
          }
        } catch (error) {
          brevoError = error?.message || 'Brevo unsubscribe failed';
        }
      }

      if (!supabaseError) {
        try {
          const supabaseResult = await supabaseDeleteUserByEmail(email);
          supabaseRemoved = Boolean(supabaseResult?.deleted);
          supabaseFound = Boolean(supabaseResult?.deleted);
        } catch (error) {
          supabaseError = error?.message || 'Supabase delete failed';
        }
      }

      const found = brevoFound || supabaseFound;
      let unsubscribeEmailSent = false;

      if (brevoRemoved) {
        try {
          const result = await sendBrevoUnsubscribeEmail({ email });
          unsubscribeEmailSent = Boolean(result?.sent);
        } catch (error) {
          unsubscribeEmailSent = false;
        }
      }

      const ok = !brevoError && !supabaseError ? true : Boolean(brevoRemoved || supabaseRemoved);
      return jsonResponse(
        {
          ok,
          found,
          brevoFound,
          brevoRemoved,
          supabaseFound,
          supabaseRemoved,
          unsubscribeEmailSent,
          brevoError,
          supabaseError,
        },
        ok ? 200 : 500
      );
    }

    // Forward to the site handler first to keep existing behavior.
    let siteOk = false;
    try {
      const siteResp = await fetch(sitePostTarget, { method: 'POST', body: formData });
      siteOk = siteResp.ok;
    } catch (error) {
      // keep going so Brevo still gets a chance
    }

    let brevoStatus = null;
    let brevoBody = null;
    let welcomeStatus = null;
    let welcomeBody = null;
    if (env.BREVO_API_KEY && email) {
      const numericListId = Number(listId || '');

      if (!Number.isFinite(numericListId) || numericListId <= 0) {
        return new Response(
          JSON.stringify({ ok: false, siteOk, error: 'Missing or invalid Brevo list id' }),
          { status: 400, headers: { 'content-type': 'application/json', ...corsHeaders } }
        );
      }
      const welcomeTemplateId = Number(env.BREVO_WELCOME_TEMPLATE_ID || '');

      const headers = {
        'api-key': env.BREVO_API_KEY,
        'content-type': 'application/json',
        accept: 'application/json',
      };

      const payload = {
        email,
        attributes: firstName ? { FIRSTNAME: firstName } : {},
        updateEnabled: true,
        emailBlacklisted: false,
        listIds: numericListId ? [numericListId] : undefined,
      };

      const brevoResp = await fetch('https://api.brevo.com/v3/contacts', {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      });
      brevoStatus = brevoResp.status;
      brevoBody = await brevoResp.text();

      if (!brevoResp.ok) {
        return new Response(
          JSON.stringify({
            ok: false,
            siteOk,
            brevoStatus,
            brevoBody: brevoBody || null,
            error: brevoBody || 'Brevo rejected the request',
          }),
          {
            status: brevoResp.status,
            headers: { 'content-type': 'application/json', ...corsHeaders },
          }
        );
      }

      if (Number.isFinite(welcomeTemplateId) && welcomeTemplateId > 0) {
        const welcomePayload = {
          to: [{ email, name: firstName || email }],
          templateId: welcomeTemplateId,
          params: firstName ? { FIRSTNAME: firstName } : {},
        };

        const welcomeResp = await fetch('https://api.brevo.com/v3/smtp/email', {
          method: 'POST',
          headers,
          body: JSON.stringify(welcomePayload),
        });

        welcomeStatus = welcomeResp.status;
        welcomeBody = await welcomeResp.text();

        if (!welcomeResp.ok) {
          return new Response(
            JSON.stringify({
              ok: false,
              siteOk,
              brevoStatus,
              welcomeStatus,
              welcomeBody: welcomeBody || null,
              error: welcomeBody || 'Brevo welcome email failed',
            }),
            {
              status: welcomeResp.status,
              headers: { 'content-type': 'application/json', ...corsHeaders },
            }
          );
        }
      }
    }

    return new Response(JSON.stringify({ ok: true, siteOk, brevoStatus, brevoBody, welcomeStatus, welcomeBody }), {
      headers: { 'content-type': 'application/json', ...corsHeaders },
    });
  },
};
