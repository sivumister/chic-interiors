# Chic Interiors — Flask + Bootstrap + Cloudflare Workers

A responsive multi-page Chic Interiors website built with **Flask** and **Bootstrap 5**. This package can run locally as a traditional Flask app and is also prepared for deployment to **Cloudflare Python Workers from GitHub**.

## Included

- Home, Shop, Product, Services, Gallery, About, Contact, Quote, Cart and Checkout pages
- Responsive Bootstrap 5 frontend
- Session-based shopping cart
- Order, quote and contact-message storage
- Password-protected admin dashboard and order-status updates
- Local SQLite database for development
- Cloudflare D1 database in production
- Gmail/SMTP email for local development
- Cloudflare Email Sending integration for production (optional until configured)
- Workers Static Assets for CSS, JavaScript and images
- GitHub → Cloudflare deployment configuration

## Run locally on Windows

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Then open `http://127.0.0.1:5000`.

If you do not want to change PowerShell's execution policy, use the virtual environment Python directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe app.py
```

## Local Gmail email testing

Edit `.env` and configure your Gmail address and a Google App Password. Never use your normal Gmail password and never commit `.env`.

## Cloudflare deployment

See **`CLOUDFLARE_DEPLOYMENT.md`** for the exact GitHub → Cloudflare process.

Main Cloudflare files:

- `worker.py` — Worker/WSGI entry point
- `wrangler.jsonc` — Workers, Static Assets and D1 configuration
- `pyproject.toml` — Python Worker dependencies
- `schema.sql` — D1 schema reference
- `tools/bundle_templates.py` — bundles Jinja templates for the Worker
- `template_bundle.py` — generated template bundle

## Admin

Set `ADMIN_PASSWORD` locally in `.env` or as a Cloudflare Worker secret, then visit `/admin/login`.

## Payments

Checkout records an order and supports the existing payment-method choices, but it deliberately does not collect card details. A Zimbabwe payment gateway can be added later after merchant credentials are available.

## Pricing note

The supplied catalog screenshots only showed limited pricing. Ready-to-hang curtains use US$25 as a starting demo price based on the screenshot; made-to-measure products use Request Quote. Confirm all prices before publishing.
