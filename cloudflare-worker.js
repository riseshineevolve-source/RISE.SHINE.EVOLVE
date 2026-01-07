// Cloudflare Worker: forwards form submissions to the site and (optionally) Brevo.
// How to wire Brevo so contacts land in your "RiseShineEvolve Subscribe" list:
//   1) In Brevo, open Contacts > Lists, click your list, and copy the numeric id from the URL.
//      For https://app.brevo.com/contact/list-listing/id/3 the numeric id is **3**.
//   2) In Cloudflare Workers > Settings > Variables, add:
//        - BREVO_API_KEY: your Brevo API key (keep it secret)
//        - BREVO_LIST_ID: 3  (the numeric id from step 1)
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
      return new Response(JSON.stringify({ ok: false, error: 'Invalid form data', detail: String(error) }), {
        status: 400,
        headers: { 'content-type': 'application/json', ...corsHeaders },
      });
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
      const doiTemplateId = Number(env.BREVO_DOI_TEMPLATE_ID || '');
      const doiRedirect = (env.BREVO_DOI_REDIRECT || '').toString().trim();
      const numericListId = Number(listId || '');

      if (!Number.isFinite(numericListId) || numericListId <= 0) {
        return new Response(
          JSON.stringify({ ok: false, siteOk, error: 'Missing or invalid Brevo list id' }),
          { status: 400, headers: { 'content-type': 'application/json', ...corsHeaders } }
        );
      }
      const welcomeTemplateId = Number(
        env.BREVO_WELCOME_TEMPLATE_ID ||
        env.BREVO_TEMPLATE_2 ||
        '2'
      );

      const headers = {
        'api-key': env.BREVO_API_KEY,
        'content-type': 'application/json',
        accept: 'application/json',
      };

      // Prefer DOI when template + redirect are configured, otherwise fall back to contact creation
      const useDoi = !!(numericListId && doiTemplateId && doiRedirect);

      const payload = useDoi
        ? {
            email,
            includeListIds: [numericListId],
            templateId: doiTemplateId,
            redirectionUrl: doiRedirect,
            attributes: firstName ? { FIRSTNAME: firstName } : {},
          }
        : {
            email,
            attributes: firstName ? { FIRSTNAME: firstName } : {},
            updateEnabled: true,
            listIds: numericListId ? [numericListId] : undefined,
          };

      const endpoint = useDoi
        ? 'https://api.brevo.com/v3/contacts/doubleOptinConfirmation'
        : 'https://api.brevo.com/v3/contacts';

      const brevoResp = await fetch(endpoint, {
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

      if (welcomeTemplateId) {
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
