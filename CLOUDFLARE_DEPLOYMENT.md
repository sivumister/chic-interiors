# Deploy Chic Interiors to Cloudflare from GitHub

This version is prepared for **Cloudflare Python Workers** while still remaining usable as a normal local Flask application.

## What changed for Cloudflare

- Flask runs through the Cloudflare Workers WSGI adapter (`worker.py`).
- Persistent application data uses **Cloudflare D1** instead of a local SQLite file when deployed.
- Bootstrap/CSS/JavaScript/images are served through **Workers Static Assets**.
- Jinja templates are bundled at build time into `template_bundle.py`.
- Worker secrets/variables replace the production `.env` file.
- Email code supports **Cloudflare Email Sending** in production while keeping Gmail/SMTP for local testing.

## 1. Test locally first (optional)

Normal Flask mode is unchanged:

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`.

## 2. Push this folder to GitHub

Create an empty GitHub repository, for example `chic-interiors`, and from this folder run:

```powershell
git init
git add .
git commit -m "Prepare Chic Interiors for Cloudflare Workers"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/chic-interiors.git
git push -u origin main
```

Do **not** commit `.env`, `.dev.vars`, Gmail app passwords, or admin passwords.

## 3. Import the GitHub repository into Cloudflare Workers

In the Cloudflare dashboard:

1. Open **Workers & Pages**.
2. Choose **Create application** / **Import a repository**.
3. Connect GitHub and select the repository.
4. Use the Worker/project name **`chic-interiors`** (it must match `name` in `wrangler.jsonc`).
5. Production branch: **`main`**.
6. If this folder is the repository root, leave Root directory as `/`.
7. Build command:

   ```bash
   python -m pip install uv && uv sync && python tools/bundle_templates.py
   ```

8. Deploy command:

   ```bash
   uv run pywrangler deploy
   ```

9. Save and deploy.

`wrangler.jsonc` declares the D1 binding as `DB`. Cloudflare can provision the resource from this binding during deployment. The app creates its required tables on first use, so there is no separate database-import step for a brand-new site.

## 4. Add production secrets and variables

In the Worker dashboard open **Settings → Variables and Secrets**.

Add these as **Secrets**:

- `SECRET_KEY` — a long random value.
- `ADMIN_PASSWORD` — a strong admin dashboard password.

Generate a Flask secret locally with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Add this as a normal **Variable** while testing:

- `BUSINESS_EMAIL=ssivuse@gmail.com`

Later change it to the Chic Interiors business inbox.

Your Gmail `SMTP_*` values are **only for local Flask testing**. Do not upload the `.env` file to Cloudflare or GitHub.

## 5. Test the deployed site

Open the generated `*.workers.dev` address and test:

- Home and images/CSS
- Shop/product pages
- Add to cart
- Checkout and order creation
- Contact form
- Quote request
- `/admin/login`
- `/admin/orders`
- Order-status changes

Orders/messages/quotes should persist in D1 even before production email sending is enabled.

## 6. Enable production email sending

The Worker is deliberately deployable **without** an email binding so that email setup cannot block the first deployment. When Cloudflare Email Sending is ready for your domain:

1. Put the Chic Interiors domain on Cloudflare DNS.
2. In Cloudflare, onboard the domain for **Email Sending**.
3. Verify any destination addresses Cloudflare asks you to verify during testing.
4. Add `MAIL_FROM`, for example `orders@chicinteriors.co.zw`, in Worker Variables. The sender must be on the domain configured for Email Sending.
5. Add this top-level section to `wrangler.jsonc` (remember the comma before it if needed):

   ```json
   "send_email": [
     {
       "name": "EMAIL",
       "remote": true
     }
   ]
   ```

6. Commit and push the change to GitHub. Cloudflare will automatically build and deploy the new commit.

The Flask code will then use the `EMAIL` binding for order confirmations, quote notifications and contact-form notifications. If the binding is absent, form/order data is still saved and the app logs that email was skipped. Cloudflare currently lists general outbound Email Sending as a Workers Paid feature; sending only to verified destination addresses can be used for limited testing on free accounts.

## 7. Connect the custom domain

After the Worker is working on its `workers.dev` address:

1. Open the Worker in Cloudflare.
2. Go to **Settings → Domains & Routes**.
3. Add the production hostname, such as `chicinteriors.co.zw` or `www.chicinteriors.co.zw`.
4. Keep the DNS zone on Cloudflare so the Worker and TLS/HTTPS can be managed there.

## 8. Future updates

Edit the code locally, then:

```powershell
git add .
git commit -m "Describe your update"
git push
```

The connected GitHub repository will trigger a new Cloudflare build/deployment.

## Important notes

- The checkout **records orders** but does not collect card details. A real payment gateway can be added later.
- Confirm all product prices before publishing.
- Keep `SECRET_KEY`, `ADMIN_PASSWORD`, SMTP passwords and other credentials out of GitHub.
- The D1 adapter is intentionally small and covers the SQL operations used by this app. If you later add complex transactions or new database features, update the adapter or use D1's native batch APIs.
