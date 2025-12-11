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
    const listIdRaw = (formData.get('brevoListId') || env.BREVO_LIST_ID || '').toString().trim();
    const actionType = (formData.get('actionType') || '').toString().toLowerCase();
    const formName = (formData.get('form-name') || '').toString().toLowerCase();
    const confirmToken = (formData.get('confirmToken') || '').toString().trim();
    const formDoiTemplate = (formData.get('doiTemplateId') || '').toString().trim();
    const formDoiRedirect = (formData.get('doiRedirect') || '').toString().trim();
    const requireDoiField = (formData.get('requireDoi') || '').toString().toLowerCase() === 'true';
    const doiTemplateId = formDoiTemplate || env.BREVO_DOI_TEMPLATE_ID;
    const doiRedirect = formDoiRedirect || env.BREVO_DOI_REDIRECT;
    const listId = listIdRaw ? Number(listIdRaw) : null;
    const hasListId = Number.isFinite(listId);
    const templateIdNum = doiTemplateId ? Number(doiTemplateId) : NaN;
    const hasDoiConfig = Number.isFinite(templateIdNum) && !!doiRedirect;
    const requireDoi = requireDoiField || !!confirmToken || hasDoiConfig;
    const isUnsubscribe = actionType === 'unsubscribe' || formName.includes('unsubscribe');

    // Lightweight contact check: skip site forwarding/DOI handling and only report Brevo list membership.
    if (actionType === 'check') {
      if (!env.BREVO_API_KEY || !hasListId || !email) {
        const missing = [];
        if (!env.BREVO_API_KEY) missing.push('BREVO_API_KEY');
        if (!hasListId) missing.push('BREVO_LIST_ID / brevoListId');
        if (!email) missing.push('email');

        return new Response(
          JSON.stringify({ ok: false, error: `Missing: ${missing.join(', ')}` }),
          { status: 400, headers: { 'content-type': 'application/json', ...corsHeaders } }
        );
      }

      try {
        const lookupResp = await fetch(`https://api.brevo.com/v3/contacts/${encodeURIComponent(email)}`, {
          headers: {
            'content-type': 'application/json',
            accept: 'application/json',
            'api-key': env.BREVO_API_KEY,
          },
        });

        const status = lookupResp.status;
        if (!lookupResp.ok) {
          const text = await lookupResp.text();
          return new Response(
            JSON.stringify({ ok: false, brevoLookupStatus: status, error: text || 'Brevo lookup failed' }),
            { status, headers: { 'content-type': 'application/json', ...corsHeaders } }
          );
        }

        const contact = await lookupResp.json();
        const listIds = Array.isArray(contact.listIds) ? contact.listIds : [];
        const alreadySubscribed = listIds.includes(listId);

        return new Response(
          JSON.stringify({ ok: true, brevoLookupStatus: status, alreadySubscribed }),
          { headers: { 'content-type': 'application/json', ...corsHeaders } }
        );
      } catch (error) {
        return new Response(
          JSON.stringify({ ok: false, error: String(error) }),
          { status: 500, headers: { 'content-type': 'application/json', ...corsHeaders } }
        );
      }
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
    let brevoLookupStatus = null;
    let alreadySubscribed = false;
    let doiAttempted = false;
    let doiStatus = null;
    let doiError = null;
    let doiFallbackUsed = false;
    let doiConfigMissing = requireDoi && !hasDoiConfig;
    let brevoErrorText = null;

    const headers = env.BREVO_API_KEY
      ? { 'content-type': 'application/json', accept: 'application/json', 'api-key': env.BREVO_API_KEY }
      : null;

    if (env.BREVO_API_KEY && hasListId && email && headers) {
      try {
        const lookupResp = await fetch(`https://api.brevo.com/v3/contacts/${encodeURIComponent(email)}`, { headers });
        brevoLookupStatus = lookupResp.status;

        if (lookupResp.ok) {
          const contact = await lookupResp.json();
          const listIds = Array.isArray(contact.listIds) ? contact.listIds : [];

          if (listIds.includes(listId) && contact.emailBlacklisted !== true) {
            alreadySubscribed = true;
            brevoStatus = brevoLookupStatus;

            return new Response(
              JSON.stringify({ ok: true, siteOk, brevoStatus, alreadySubscribed: true }),
              { headers: { 'content-type': 'application/json', ...corsHeaders } }
            );
          }
        }
      } catch (_) {
        // If the lookup fails, continue to normal DOI handling.
      }
    }

    if (requireDoi) {
      const missing = [];
      if (!env.BREVO_API_KEY) missing.push('BREVO_API_KEY');
      if (!hasListId) missing.push('BREVO_LIST_ID / brevoListId');
      if (!Number.isFinite(templateIdNum)) missing.push('BREVO_DOI_TEMPLATE_ID / doiTemplateId');
      if (!doiRedirect) missing.push('BREVO_DOI_REDIRECT / doiRedirect');

      if (missing.length) {
        return new Response(
          JSON.stringify({
            ok: false,
            siteOk,
            brevoStatus: null,
            error: `Missing required Brevo settings: ${missing.join(', ')}`,
            missing,
          }),
          { status: 400, headers: { 'content-type': 'application/json', ...corsHeaders } }
        );
      }
    }

    if (env.BREVO_API_KEY && email && headers) {
      const baseAttributes = firstName ? { FIRSTNAME: firstName } : {};

      const includeListIds = hasListId ? [listId] : undefined;

      const sendFallbackConfirmation = async () => {
        doiFallbackUsed = true;
        doiConfigMissing = doiConfigMissing || !hasDoiConfig;

        const fallbackRedirect = doiRedirect || sitePostTarget;
        const separator = fallbackRedirect.includes('?') ? '&' : '?';
        const confirmLink = `${fallbackRedirect}${separator}brevoConfirmed=1&email=${encodeURIComponent(email)}` +
          `${confirmToken ? `&confirmToken=${encodeURIComponent(confirmToken)}` : ''}`;

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
        brevoStatus = brevoStatus || smtpResp.status;

        if (!smtpResp.ok) {
          const errorText = await smtpResp.text();
          return { ok: false, status: smtpResp.status, error: errorText || 'Fallback confirmation email failed' };
        }

        return { ok: true, status: smtpResp.status };
      };
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
        const tryDoi = hasDoiConfig;

        if (tryDoi) {
          doiAttempted = true;
          if (!hasListId) {
            return new Response(
              JSON.stringify({
                ok: false,
                siteOk,
                brevoStatus: null,
                error: 'Brevo double opt-in requires a numeric BREVO_LIST_ID / brevoListId',
              }),
              { status: 400, headers: { 'content-type': 'application/json', ...corsHeaders } }
            );
          }

          if (Number.isNaN(templateIdNum)) {
            return new Response(
              JSON.stringify({
                ok: false,
                siteOk,
                brevoStatus: null,
                error: 'Brevo double opt-in requires a numeric BREVO_DOI_TEMPLATE_ID / doiTemplateId',
              }),
              { status: 400, headers: { 'content-type': 'application/json', ...corsHeaders } }
            );
          }

          if (!doiRedirect) {
            return new Response(
              JSON.stringify({
                ok: false,
                siteOk,
                brevoStatus: null,
                error: 'Brevo double opt-in requires BREVO_DOI_REDIRECT / doiRedirect',
              }),
              { status: 400, headers: { 'content-type': 'application/json', ...corsHeaders } }
            );
          }

          const separator = doiRedirect.includes('?') ? '&' : '?';
          const doiPayload = {
            email,
            templateId: Number(doiTemplateId),
            attributes: baseAttributes,
            redirectionUrl: `${doiRedirect}${separator}brevoConfirmed=1&email=${encodeURIComponent(email)}${confirmToken ? `&confirmToken=${encodeURIComponent(confirmToken)}` : ''}`,
            includeListIds: includeListIds,
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
            brevoErrorText = errorText || null;
            doiError = errorText || 'Brevo double opt-in rejected the request';
            const fallback = requireDoi ? await sendFallbackConfirmation() : { ok: false };

            if (!fallback.ok) {
              return new Response(
                JSON.stringify({
                  ok: false,
                  siteOk,
                  brevoStatus,
                  doiAttempted,
                  doiStatus,
                  doiError,
                  brevoErrorText,
                  doiFallbackUsed,
                  requireDoi,
                  doiConfigMissing: false,
                  doiTemplateId: doiTemplateId || null,
                  doiRedirect: doiRedirect || null,
                  fallbackError: fallback.error || null,
                  fallbackStatus: fallback.status || null,
                }),
                { status: fallback.status || doiResp.status, headers: { 'content-type': 'application/json', ...corsHeaders } }
              );
            }
          }
        } else if (requireDoi) {
          // Fallback path: send a transactional confirmation email when DOI config is missing.
          const fallback = await sendFallbackConfirmation();

          if (!fallback.ok) {
            doiError = fallback.error || null;
            doiStatus = fallback.status || null;
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
                fallbackStatus: fallback.status || null,
              }),
              { status: fallback.status || 500, headers: { 'content-type': 'application/json', ...corsHeaders } }
            );
          }
        } else if (hasDoiConfig) {
          if (!hasListId) {
            return new Response(
              JSON.stringify({
                ok: false,
                siteOk,
                brevoStatus: null,
                error: 'Brevo double opt-in requires a numeric BREVO_LIST_ID / brevoListId',
              }),
              { status: 400, headers: { 'content-type': 'application/json', ...corsHeaders } }
            );
          }

          const separator = doiRedirect.includes('?') ? '&' : '?';
          const payload = {
            email,
            attributes: baseAttributes,
            redirectionUrl: `${doiRedirect}${separator}brevoConfirmed=1&email=${encodeURIComponent(email)}${confirmToken ? `&confirmToken=${encodeURIComponent(confirmToken)}` : ''}`,
            includeListIds: includeListIds,
            templateId: Number(doiTemplateId),
          };

          const brevoResp = await fetch('https://api.brevo.com/v3/contacts/doubleOptinConfirmation', {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
          });
          brevoStatus = brevoResp.status;

          if (!brevoResp.ok) {
            const errorText = await brevoResp.text();
            brevoErrorText = errorText || null;
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
        brevoErrorText,
        doiFallbackUsed,
        requireDoi,
        doiConfigMissing,
        alreadySubscribed,
        brevoLookupStatus,
        doiTemplateId: doiTemplateId || null,
        doiRedirect: doiRedirect || null,
      }),
      {
        headers: { 'content-type': 'application/json', ...corsHeaders },
      }
    );
  },
};
