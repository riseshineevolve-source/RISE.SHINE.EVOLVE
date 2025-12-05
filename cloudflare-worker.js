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

    let formData;
    try {
      formData = await request.formData();
    } catch (error) {
      return new Response(JSON.stringify({ ok: false, error: 'Invalid form data', detail: String(error) }), {
        status: 400,
        headers: { 'content-type': 'application/json', ...corsHeaders },
      });
    }

    const firstName = (formData.get('firstName') || '').toString().trim();
    const email = (formData.get('email') || '').toString().trim();
    const listId = formData.get('brevoListId') || env.BREVO_LIST_ID;

    // Forward to the site handler first to keep existing behavior.
    let siteOk = false;
    try {
      const siteResp = await fetch(sitePostTarget, { method: 'POST', body: formData });
      siteOk = siteResp.ok;
    } catch (error) {
      // keep going so Brevo still gets a chance
    }

    let brevoStatus = null;
    if (env.BREVO_API_KEY && email) {
      const payload = {
        email,
        attributes: firstName ? { FIRSTNAME: firstName } : {},
        updateEnabled: true,
      };
      if (listId) payload.listIds = [Number(listId)];

      const brevoResp = await fetch('https://api.brevo.com/v3/contacts', {
        method: 'POST',
        headers: {
          'api-key': env.BREVO_API_KEY,
          'content-type': 'application/json',
          accept: 'application/json',
        },
        body: JSON.stringify(payload),
      });
      brevoStatus = brevoResp.status;

      if (!brevoResp.ok) {
        const errorText = await brevoResp.text();
        return new Response(
          JSON.stringify({ ok: false, siteOk, brevoStatus, error: errorText || 'Brevo rejected the request' }),
          {
            status: brevoResp.status,
            headers: { 'content-type': 'application/json', ...corsHeaders },
          }
        );
      }
    }

    return new Response(JSON.stringify({ ok: true, siteOk, brevoStatus }), {
      headers: { 'content-type': 'application/json', ...corsHeaders },
    });
  },
};
