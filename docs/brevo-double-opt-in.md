# Brevo double opt-in and confirmation link setup

These steps explain which template to use, how the confirmation link is generated, and what to configure in Cloudflare so the email arrives and the redirect works.

## 1) Choose the confirmation template in Brevo
- Open **Brevo → Campaigns → Templates** and pick the email you want to send as the confirmation request. The numeric ID shown in the template URL is what you pass to `BREVO_DOI_TEMPLATE_ID`.
- The template itself should contain a single confirmation button or link using Brevo’s built-in double opt-in placeholder (you do **not** paste your own link). Brevo injects the confirmation URL automatically when the worker calls the `/v3/contacts/doubleOptinConfirmation` endpoint.

## 2) Where the confirmation link comes from
- You do not generate or paste a link into the template. Brevo inserts the confirmation link for you when the worker triggers the double opt-in API.
- After the user clicks, Brevo redirects to the `BREVO_DOI_REDIRECT` URL you configured in the worker, appending `?brevoConfirmed=1&email=...&confirmToken=...` so the site can unlock GIFTS access.

## 3) Cloudflare Worker configuration
- `BREVO_API_KEY`: your Brevo API key.
- `BREVO_LIST_ID`: numeric list ID to subscribe new contacts to.
- `BREVO_DOI_TEMPLATE_ID`: numeric ID of the template chosen in step 1.
- `BREVO_DOI_REDIRECT`: the live URL Brevo should send users to after they click the confirmation button.

With those variables set, the worker sends the double opt-in request to Brevo, Brevo emails your chosen template, and the built-in confirmation link routes users back through your redirect URL with the confirmation flags.
