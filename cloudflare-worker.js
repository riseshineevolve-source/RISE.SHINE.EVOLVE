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
    const actionType = (formData.get('actionType') || '').toString().toLowerCase();
    const formName = (formData.get('form-name') || '').toString().toLowerCase();
    const confirmToken = (formData.get('confirmToken') || '').toString().trim();
    const formDoiTemplate = (formData.get('doiTemplateId') || '').toString().trim();
    const formDoiRedirect = (formData.get('doiRedirect') || '').toString().trim();
    const requireDoi = (formData.get('requireDoi') || '').toString().toLowerCase() === 'true' || !!confirmToken;
    const doiTemplateId = formDoiTemplate || env.BREVO_DOI_TEMPLATE_ID;
    const doiRedirect = formDoiRedirect || env.BREVO_DOI_REDIRECT;
    const hasDoiConfig = !!(doiTemplateId && doiRedirect);
    const isUnsubscribe = actionType === 'unsubscribe' || formName.includes('unsubscribe');

    // Forward to the site handler first to keep existing behavior.
    let siteOk = false;
    try {
      const siteResp = await fetch(sitePostTarget, { method: 'POST', body: formData });
      siteOk = siteResp.ok;
    } catch (error) {
      // keep going so Brevo still gets a chance
    }

    let brevoStatus = null;
    let doiAttempted = false;
    let doiStatus = null;
    let doiError = null;
    let doiFallbackUsed = false;
    if (env.BREVO_API_KEY && email) {
      if (isUnsubscribe) {
        const unlinkListIds = listId ? [Number(listId)] : undefined;
        const payload = {
          emailBlacklisted: true,
          ...(unlinkListIds ? { unlinkListIds } : {}),
        };

        const brevoResp = await fetch(`https://api.brevo.com/v3/contacts/${encodeURIComponent(email)}`, {
          method: 'PUT',
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
            JSON.stringify({ ok: false, siteOk, brevoStatus, error: errorText || 'Brevo unsubscribe failed' }),
            {
              status: brevoResp.status,
              headers: { 'content-type': 'application/json', ...corsHeaders },
            }
          );
        }
      } else {
        const baseAttributes = firstName ? { FIRSTNAME: firstName } : {};
        const includeListIds = listId ? [Number(listId)] : undefined;
        const headers = { 'content-type': 'application/json', accept: 'application/json', 'api-key': env.BREVO_API_KEY };

        const tryDoi = hasDoiConfig;
        if (requireDoi && !tryDoi) {
          return new Response(
            JSON.stringify({
              ok: false,
              siteOk,
              brevoStatus: null,
              doiAttempted,
              doiStatus,
              doiError: 'Double opt-in is required but no template/redirect was provided.',
              doiFallbackUsed,
              requireDoi,
              doiConfigMissing: true,
              doiTemplateId: doiTemplateId || null,
              doiRedirect: doiRedirect || null,
            }),
            { status: 400, headers: { 'content-type': 'application/json', ...corsHeaders } }
          );
        }

        if (tryDoi) {
          doiAttempted = true;
          const doiPayload = {
            email,
            templateId: Number(doiTemplateId),
            attributes: baseAttributes,
            redirectionUrl: `${doiRedirect}?brevoConfirmed=1&email=${encodeURIComponent(email)}${confirmToken ? `&confirmToken=${encodeURIComponent(confirmToken)}` : ''}`,
            includeListIds: includeListIds || [],
          };

          const doiResp = await fetch('https://api.brevo.com/v3/contacts/doubleOptinConfirmation', {
            method: 'POST',
            headers,
            body: JSON.stringify(doiPayload),
          });
          brevoStatus = doiResp.status;
          doiStatus = doiResp.status;

          if (!doiResp.ok) {
            const errorText = await doiResp.text();
            doiError = errorText || 'Brevo double opt-in rejected the request';
            return new Response(
              JSON.stringify({
                ok: false,
                siteOk,
                brevoStatus,
                doiAttempted,
                doiStatus,
                doiError,
                doiFallbackUsed,
                requireDoi,
                doiConfigMissing: false,
                doiTemplateId: doiTemplateId || null,
                doiRedirect: doiRedirect || null,
              }),
              { status: doiResp.status, headers: { 'content-type': 'application/json', ...corsHeaders } }
            );
          }
        } else if (requireDoi) {
          // Fallback path: send a transactional confirmation email when DOI config is missing.
          doiFallbackUsed = true;

          // Create/update the contact on the list so Brevo keeps the same roster as the site.
          const fallbackPayload = {
            email,
            attributes: baseAttributes,
            updateEnabled: true,
            ...(includeListIds ? { listIds: includeListIds } : {}),
          };

          const contactResp = await fetch('https://api.brevo.com/v3/contacts', {
            method: 'POST',
            headers,
            body: JSON.stringify(fallbackPayload),
          });
          brevoStatus = contactResp.status;

          if (!contactResp.ok) {
            const errorText = await contactResp.text();
            return new Response(
              JSON.stringify({
                ok: false,
                siteOk,
                brevoStatus,
                doiAttempted,
                doiStatus,
                doiError: errorText || 'Brevo rejected the fallback contact creation',
                doiFallbackUsed,
                requireDoi,
                doiConfigMissing: true,
                doiTemplateId: doiTemplateId || null,
                doiRedirect: doiRedirect || null,
              }),
              { status: contactResp.status, headers: { 'content-type': 'application/json', ...corsHeaders } }
            );
          }

          // Build a manual confirmation email with the confirmToken/redirect when DOI is missing.
          const fallbackRedirect = doiRedirect || sitePostTarget;
          const separator = fallbackRedirect.includes('?') ? '&' : '?';
          const confirmLink = `${fallbackRedirect}${separator}brevoConfirmed=1&email=${encodeURIComponent(
            email
          )}${confirmToken ? `&confirmToken=${encodeURIComponent(confirmToken)}` : ''}`;

          const senderEmail = (env.BREVO_SENDER_EMAIL || '').trim() || 'no-reply@rise-shine-evolve.com';
          const senderName = (env.BREVO_SENDER_NAME || '').trim() || 'Rise Shine Evolve';

          const smtpPayload = {
            sender: { email: senderEmail, name: senderName },
            to: [{ email, name: firstName || 'Friend' }],
            subject: 'Please confirm your subscription',
            htmlContent: `
              <p>Hi${firstName ? ` ${firstName}` : ''},</p>
              <p>Click the button below to confirm your subscription and unlock GIFTS:</p>
              <p><a href="${confirmLink}" style="background:#8A2BE2;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none;">Confirm my subscription</a></p>
              <p>Or copy this link if the button does not work:<br>${confirmLink}</p>
            `,
            textContent: `Please confirm your subscription: ${confirmLink}`,
          };

          const smtpResp = await fetch('https://api.brevo.com/v3/smtp/email', {
            method: 'POST',
            headers,
            body: JSON.stringify(smtpPayload),
          });

          doiStatus = smtpResp.status;

          if (!smtpResp.ok) {
            const errorText = await smtpResp.text();
            doiError = errorText || 'Fallback confirmation email failed';
            return new Response(
              JSON.stringify({
                ok: false,
                siteOk,
                brevoStatus,
                doiAttempted,
                doiStatus,
                doiError,
                doiFallbackUsed,
                requireDoi,
                doiConfigMissing: true,
                doiTemplateId: doiTemplateId || null,
                doiRedirect: doiRedirect || null,
              }),
              { status: smtpResp.status, headers: { 'content-type': 'application/json', ...corsHeaders } }
            );
          }
        } else {
          const payload = {
            email,
            attributes: baseAttributes,
            updateEnabled: true,
            ...(includeListIds ? { listIds: includeListIds } : {}),
          };

          const brevoResp = await fetch('https://api.brevo.com/v3/contacts', {
            method: 'POST',
            headers,
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
      }
    }

    return new Response(
      JSON.stringify({
        ok: true,
        siteOk,
        brevoStatus,
        doiAttempted,
        doiStatus,
        doiError,
        doiFallbackUsed,
        requireDoi,
        doiConfigMissing: false,
        doiTemplateId: doiTemplateId || null,
        doiRedirect: doiRedirect || null,
      }),
      {
        headers: { 'content-type': 'application/json', ...corsHeaders },
      }
    );
  },
};
