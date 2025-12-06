# Brevo double opt-in and confirmation link setup

These steps explain which template to use, how the confirmation link is generated, and what to configure in Cloudflare so the email arrives and the redirect works.

## 1) Create the confirmation template in Brevo (with a working link)
- Go to **Transactional → Templates** (or **Campaigns → Templates** if that’s where your account shows them) and click **Create a new template**.
- In **Design**, add a **Button** (or text link) and set its URL to Brevo’s placeholder: `{{ doubleoptinUrl }}`. In the drag-and-drop editor you can click **Personalize → Double opt-in confirmation link** to insert it automatically.
- Save and **Activate** the template. The numeric ID in the URL (e.g., `/templates/123`) is what you set as `BREVO_DOI_TEMPLATE_ID`.
- Note: sending a “test email” from the template editor will not include a live confirmation link. The link only appears when Brevo sends the template via the double opt-in API call.

## 2) Where the confirmation link comes from
- You do not generate or paste a link into the template. Brevo inserts the confirmation link for you when the worker triggers the double opt-in API.
- After the user clicks, Brevo redirects to the `BREVO_DOI_REDIRECT` URL you configured in the worker, appending `?brevoConfirmed=1&email=...&confirmToken=...` so the site can unlock GIFTS access.

## 3) Cloudflare Worker configuration
- `BREVO_API_KEY`: your Brevo API key.
- `BREVO_LIST_ID`: numeric list ID to subscribe new contacts to.
- `BREVO_DOI_TEMPLATE_ID`: numeric ID of the template chosen in step 1.
- `BREVO_DOI_REDIRECT`: the live URL Brevo should send users to after they click the confirmation button.

With those variables set, the worker sends the double opt-in request to Brevo, Brevo emails your chosen template, and the built-in confirmation link routes users back through your redirect URL with the confirmation flags.

If you haven’t populated the worker variables yet, you can also pass `BREVO_DOI_TEMPLATE_ID` and `BREVO_DOI_REDIRECT` from the page: fill them in `index.html` near the other Brevo constants. Alternatively, add URL parameters like `?doiTemplateId=123&doiRedirect=https://your.site/` (they’ll be saved in localStorage) and the form will forward them to the worker so the double opt-in call can still succeed.
