# AURA — Django E-commerce Store

A complete, production-minded e-commerce store: product catalog, shopping cart,
checkout with order processing, and user accounts. Built with Django + server-rendered
templates and a custom responsive UI (no CSS framework).

## Features

- **Catalog** — categories, keyword search, pagination, product detail pages with related items.
- **Cart** — works for guests (session-based) and logged-in users (DB-backed). A guest cart is **merged into the user's cart on login/signup**.
- **Checkout & orders** — shipping form, atomic order placement that **locks stock rows to prevent overselling**, and snapshots unit prices so historical orders never change. Order confirmation + order history.
- **Accounts** — registration, login, logout, profile. Password validation enabled.
- **Admin** — manage products, categories, and orders at `/admin/` (inline order items, editable price/stock).
- **Security** — CSRF protection, auto-escaped templates, ORM (no raw SQL), and HTTPS/HSTS/secure-cookie hardening that activates automatically when `DEBUG=False`.

## Tech stack

| Layer    | Choice                                  |
|----------|-----------------------------------------|
| Backend  | Django 5.1                              |
| Database | SQLite (default) · Postgres (via `DATABASE_URL`) |
| Frontend | Django templates, vanilla CSS + JS      |
| Static   | WhiteNoise (compressed, hashed)         |
| Images   | Pillow (placeholder generation in seed) |

## Quick start

```bash
# 1. (Recommended) create a virtual environment
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env        # the defaults work for local development

# 4. Set up the database
python manage.py migrate

# 5. Load demo products (generates placeholder images)
python manage.py seed

# 6. Create an admin account
python manage.py createsuperuser

# 7. Run it
python manage.py runserver
```

Open <http://127.0.0.1:8000/> for the store and <http://127.0.0.1:8000/admin/> for the dashboard.

## Project layout

```
config/            # Settings, root URLconf, WSGI/ASGI
store/             # Catalog, cart, orders
  models.py        #   Category, Product, Cart, CartItem, Order, OrderItem
  services.py      #   Cart resolution, login-merge, atomic checkout (stock-safe)
  views.py         #   Catalog, cart, checkout, orders
  context_processors.py  # Cart badge for every page
  templatetags/    #   query_transform (pagination keeps filters)
  management/commands/seed.py
accounts/          # Registration / login / profile (+ cart merge on auth)
templates/         # base, store/*, accounts/*
static/            # css/styles.css, js/main.js
```

## Notes on key decisions

- **Cart merge timing.** Django cycles the session key during `login()`, so the
  anonymous session key is captured *before* logging in, then used to merge the
  guest cart. See `accounts/views.py` and `store/services.merge_session_cart`.
- **Stock integrity.** `place_order` runs in a transaction and uses
  `select_for_update()` on products (ordered by pk to avoid deadlocks), so two
  shoppers can't buy the last unit twice.
- **Price snapshots.** `OrderItem` stores the unit price and product name at
  purchase time; changing a product's price later never rewrites past orders.

## Going to production

1. Set `DEBUG=False`, a strong `SECRET_KEY`, and real `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS`.
2. Point `DATABASE_URL` at Postgres and add `psycopg[binary]` (already listed, commented) to requirements.
3. `python manage.py collectstatic`
4. Serve with `gunicorn config.wsgi` behind your reverse proxy.
5. **Payments are simulated** — the checkout marks orders as paid without a real charge.
   To accept money, create a payment intent (e.g. Stripe) before `place_order` and
   only finalize the order on a confirmed charge/webhook. The seam for this is marked
   in `store/views.checkout`.
