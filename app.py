import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from flask import (
    Flask, Response, abort, flash, has_request_context, redirect, render_template,
    request, send_from_directory, session, url_for
)
from jinja2 import DictLoader

BASE_DIR = Path(__file__).resolve().parent

# Cloudflare Python Workers expose ``workers``, ``js`` and ``pyodide`` inside
# the Worker runtime. Checking all three avoids accidentally treating a normal
# local Python process as a Worker merely because ``workers-py`` is installed.
try:
    from workers import wsgi  # noqa: F401
    from js import Object
    from pyodide.ffi import run_sync, to_js as _to_js
    from template_bundle import TEMPLATES
    WORKER_RUNTIME = True
except ImportError:
    WORKER_RUNTIME = False

if not WORKER_RUNTIME:
    import smtplib
    import sqlite3
    from email.message import EmailMessage

    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / '.env')

app = Flask(__name__, static_folder=None)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-change-this-secret-key')
app.config['DATABASE'] = os.getenv(
    'DATABASE_PATH', str(BASE_DIR / 'instance' / 'chic_interiors.db')
)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

if WORKER_RUNTIME:
    # Flask normally reads Jinja templates from disk. Python Workers bundle
    # Python modules, so deployment builds generate template_bundle.py and use
    # an in-memory Jinja loader instead.
    app.jinja_loader = DictLoader(TEMPLATES)

BUSINESS = {
    'name': 'Chic Interiors',
    'phone_display': '+263 77 382 4395',
    'phone': '263773824395',
    'email': 'tarirobetsy@gmail.com',
    'instagram': '@tarirobetsy',
    'instagram_url': 'https://www.instagram.com/tarirobetsy/',
    'location': 'Chelsea Cl, Harare, Zimbabwe',
    'hours': 'Monday–Saturday · 08:00–17:00',
    'whatsapp': 'https://wa.me/263773824395',
}

PRODUCTS = [
    {
        'slug': 'ready-to-hang-curtains',
        'name': 'Ready-to-Hang Curtains',
        'category': 'Curtains',
        'description': 'Elegant ready-to-hang curtains. The catalog indicates options ranging around US$25–US$40 for 3 m selections.',
        'image': 'ready-hang.jpg',
        'price': 25.00,
        'price_label': 'From US$25',
        'purchasable': True,
    },
    {
        'slug': 'lace-curtains',
        'name': 'Lace Curtains',
        'category': 'Curtains',
        'description': 'Light linen, heavy linen and printed lace curtain options for soft, airy interiors.',
        'image': 'lace-curtains.jpg',
        'price': None,
        'price_label': 'Request quote',
        'purchasable': False,
    },
    {
        'slug': 'roller-blinds',
        'name': 'Roller Blinds',
        'category': 'Blinds',
        'description': 'Made-to-measure roller blinds for kitchens, bedrooms, offices and living spaces.',
        'image': 'roller-blinds.jpg',
        'price': None,
        'price_label': 'From catalog: US$75/sqm',
        'purchasable': False,
    },
    {
        'slug': 'natural-blockout-curtains',
        'name': 'Natural Colour Blockout Curtains',
        'category': 'Curtains',
        'description': 'Natural-tone 70%–90% blockout curtains for privacy, light control and a calm neutral finish.',
        'image': 'natural-blockout.jpg',
        'price': None,
        'price_label': 'Request quote',
        'purchasable': False,
    },
    {
        'slug': 'pink-curtains',
        'name': 'Pink Curtains',
        'category': 'Curtains',
        'description': 'Soft pink blockout curtains, ideal for bedrooms, nurseries and warm contemporary rooms.',
        'image': 'pink-curtains.jpg',
        'price': None,
        'price_label': 'Request quote',
        'purchasable': False,
    },
    {
        'slug': 'blue-curtains',
        'name': 'Blue Curtains',
        'category': 'Curtains',
        'description': 'Available in jacquard and blockout options with a bold, clean blue finish.',
        'image': 'blue-curtains.jpg',
        'price': None,
        'price_label': 'Request quote',
        'purchasable': False,
    },
    {
        'slug': 'grey-blockout-curtains',
        'name': 'Grey Blockout Curtains',
        'category': 'Curtains',
        'description': '70%–90% sunblock curtain options in a versatile grey palette.',
        'image': 'grey-blockout.jpg',
        'price': None,
        'price_label': 'Request quote',
        'purchasable': False,
    },
    {
        'slug': 'natural-colour-curtains',
        'name': 'Natural Colour Curtains',
        'category': 'Curtains',
        'description': 'Jacquard and linen curtain options in understated natural colours.',
        'image': 'natural-color.jpg',
        'price': None,
        'price_label': 'Request quote',
        'purchasable': False,
    },
    {
        'slug': 'curtain-hardware',
        'name': 'Tracks, Rods & Accessories',
        'category': 'Hardware',
        'description': 'Wave tracks, rods and curtain accessories selected to suit the finished design.',
        'image': 'hardware.jpg',
        'price': None,
        'price_label': 'Request quote',
        'purchasable': False,
    },
    {
        'slug': 'motorised-wave-curtains',
        'name': 'Motorised Wave Curtains',
        'category': 'Motorised',
        'description': 'Imported motorised wave curtain solutions for effortless opening and closing.',
        'image': 'motorised.jpg',
        'price': None,
        'price_label': 'Request consultation',
        'purchasable': False,
    },
    {
        'slug': 'premier-wave-curtains',
        'name': 'Wave Curtains · Premier Range',
        'category': 'Curtains',
        'description': 'A premium wave-curtain range with a smooth, modern drape and made-to-measure finish.',
        'image': 'wave-curtains.jpg',
        'price': None,
        'price_label': 'Request quote',
        'purchasable': False,
    },
]

PRODUCT_MAP = {p['slug']: p for p in PRODUCTS}

SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    city TEXT NOT NULL,
    notes TEXT,
    payment_method TEXT NOT NULL,
    total REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'New'
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_slug TEXT NOT NULL,
    product_name TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    subtotal REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    subject TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    product TEXT,
    details TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'New'
);
"""

_D1_SCHEMA_READY = False


def _worker_env():
    if not WORKER_RUNTIME or not has_request_context():
        return None
    return request.environ.get('workers.env')


def _binding(env, name):
    if env is None:
        return None
    try:
        return getattr(env, name)
    except (AttributeError, TypeError):
        return None


def get_setting(name, default=None):
    """Read a setting from Worker bindings first, then local environment."""
    env = _worker_env()
    value = _binding(env, name)
    if value is not None:
        text = str(value)
        if text and text != 'undefined':
            return text
    return os.getenv(name, default)


def configure_worker(env):
    """Apply Worker secrets before Flask opens the request session."""
    secret = _binding(env, 'SECRET_KEY')
    if secret is not None and str(secret) not in ('', 'undefined'):
        app.config['SECRET_KEY'] = str(secret)
    app.config['SESSION_COOKIE_SECURE'] = True


def _js_row_to_dict(row):
    try:
        value = row.to_py()
        if isinstance(value, dict):
            return value
    except Exception:
        pass
    # D1 rows are normally JsProxy objects. This fallback is only for unusual
    # runtimes/tests where a mapping-like Python object is returned instead.
    try:
        return dict(row)
    except Exception:
        return row


class D1Cursor:
    def __init__(self, rows=None, lastrowid=None):
        self._rows = rows or []
        self.lastrowid = lastrowid

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class D1Connection:
    """Small sqlite3-like adapter around the Cloudflare D1 binding."""
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        stmt = self.db.prepare(sql)
        if params:
            stmt = stmt.bind(*params)
        operation = sql.lstrip().split(None, 1)[0].upper() if sql.strip() else ''
        if operation in {'SELECT', 'PRAGMA', 'WITH'}:
            result = run_sync(stmt.all())
            raw_rows = getattr(result, 'results', None) or []
            rows = [_js_row_to_dict(row) for row in raw_rows]
            return D1Cursor(rows=rows)

        result = run_sync(stmt.run())
        meta = getattr(result, 'meta', None)
        last_row_id = getattr(meta, 'last_row_id', None) if meta is not None else None
        try:
            last_row_id = int(last_row_id) if last_row_id is not None else None
        except (TypeError, ValueError):
            last_row_id = None
        return D1Cursor(lastrowid=last_row_id)

    def executescript(self, script):
        run_sync(self.db.exec(script))
        return self


def _ensure_d1_schema(db):
    global _D1_SCHEMA_READY
    if _D1_SCHEMA_READY:
        return
    run_sync(db.exec(SCHEMA_SQL))
    _D1_SCHEMA_READY = True


def get_db():
    if WORKER_RUNTIME:
        env = _worker_env()
        d1 = _binding(env, 'DB')
        if d1 is None:
            raise RuntimeError("Cloudflare D1 binding 'DB' is not configured.")
        _ensure_d1_schema(d1)
        return D1Connection(d1)

    db_path = Path(app.config['DATABASE'])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as db:
        db.executescript(SCHEMA_SQL)


def _python_to_js(value):
    return _to_js(value, dict_converter=Object.fromEntries)


def send_email(subject, body, to_email, reply_to=None):
    """Send via Cloudflare Email Service in production, Gmail/SMTP locally."""
    if WORKER_RUNTIME:
        env = _worker_env()
        email_binding = _binding(env, 'EMAIL')
        if email_binding is None:
            app.logger.info(
                'EMAIL NOT SENT (Cloudflare EMAIL binding not configured) | %s | to=%s',
                subject, to_email
            )
            return False

        from_email = get_setting('MAIL_FROM', BUSINESS['email'])
        payload = {
            'to': to_email,
            'from': from_email,
            'subject': subject,
            'text': body,
        }
        if reply_to:
            payload['replyTo'] = reply_to
        run_sync(email_binding.send(_python_to_js(payload)))
        return True

    host = os.getenv('SMTP_HOST')
    user = os.getenv('SMTP_USER')
    password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('MAIL_FROM', user or BUSINESS['email'])
    port = int(os.getenv('SMTP_PORT', '587'))
    use_ssl = os.getenv('SMTP_SSL', 'false').lower() == 'true'

    if not all([host, user, password, to_email]):
        app.logger.info(
            'EMAIL NOT SENT (SMTP not configured) | %s | to=%s\n%s',
            subject, to_email, body
        )
        return False

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    if reply_to:
        msg['Reply-To'] = reply_to
    msg.set_content(body)

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, timeout=20) as server:
            server.login(user, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(user, password)
            server.send_message(msg)
    return True

def cart_details():
    cart = session.get('cart', {})
    items = []
    total = 0.0
    count = 0
    for slug, qty in cart.items():
        product = PRODUCT_MAP.get(slug)
        if not product or not product['purchasable'] or product['price'] is None:
            continue
        qty = max(1, int(qty))
        subtotal = product['price'] * qty
        items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
        total += subtotal
        count += qty
    return items, round(total, 2), count


@app.get('/static/<path:filename>', endpoint='static')
def static_asset(filename):
    """Serve local static files or proxy Cloudflare Workers Static Assets."""
    env = _worker_env()
    assets = _binding(env, 'ASSETS') if env is not None else None
    if WORKER_RUNTIME and assets is not None:
        asset_response = run_sync(assets.fetch(f"https://assets.local/{filename}"))
        body = run_sync(asset_response.bytes())
        return Response(
            body,
            status=asset_response.status,
            headers=asset_response.headers,
        )
    return send_from_directory(BASE_DIR / 'static', filename)


@app.context_processor
def inject_globals():
    _, _, cart_count = cart_details()
    return {'business': BUSINESS, 'cart_count': cart_count, 'year': datetime.now().year}


@app.route('/')
def home():
    featured = PRODUCTS[:6]
    return render_template('home.html', featured=featured)


@app.route('/shop')
def shop():
    categories = sorted({p['category'] for p in PRODUCTS})
    return render_template('shop.html', products=PRODUCTS, categories=categories)


@app.route('/product/<slug>')
def product_detail(slug):
    product = PRODUCT_MAP.get(slug)
    if not product:
        abort(404)
    related = [p for p in PRODUCTS if p['category'] == product['category'] and p['slug'] != slug][:3]
    return render_template('product_detail.html', product=product, related=related)


@app.post('/cart/add/<slug>')
def add_to_cart(slug):
    product = PRODUCT_MAP.get(slug)
    if not product or not product['purchasable'] or product['price'] is None:
        flash('This item is made-to-measure. Please request a quote instead.', 'info')
        return redirect(url_for('quote', product=slug))
    try:
        qty = max(1, min(20, int(request.form.get('quantity', 1))))
    except ValueError:
        qty = 1
    cart = session.get('cart', {})
    cart[slug] = int(cart.get(slug, 0)) + qty
    session['cart'] = cart
    session.modified = True
    flash(f'{product["name"]} added to your cart.', 'success')
    return redirect(request.referrer or url_for('cart'))


@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        cart_data = session.get('cart', {})
        for slug in list(cart_data.keys()):
            raw = request.form.get(f'qty_{slug}', cart_data[slug])
            try:
                qty = int(raw)
            except ValueError:
                qty = cart_data[slug]
            if qty <= 0:
                cart_data.pop(slug, None)
            else:
                cart_data[slug] = min(qty, 20)
        session['cart'] = cart_data
        session.modified = True
        flash('Cart updated.', 'success')
        return redirect(url_for('cart'))
    items, total, _ = cart_details()
    return render_template('cart.html', items=items, total=total)


@app.post('/cart/remove/<slug>')
def remove_from_cart(slug):
    cart_data = session.get('cart', {})
    cart_data.pop(slug, None)
    session['cart'] = cart_data
    session.modified = True
    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    items, total, _ = cart_details()
    if not items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('shop'))

    if request.method == 'POST':
        fields = {
            'customer_name': request.form.get('name', '').strip(),
            'email': request.form.get('email', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'address': request.form.get('address', '').strip(),
            'city': request.form.get('city', '').strip(),
            'notes': request.form.get('notes', '').strip(),
            'payment_method': request.form.get('payment_method', 'Bank Transfer').strip(),
        }
        required = ['customer_name', 'email', 'phone', 'address', 'city']
        if any(not fields[k] for k in required) or '@' not in fields['email']:
            flash('Please complete all required fields with a valid email address.', 'danger')
            return render_template('checkout.html', items=items, total=total, form=request.form)

        order_number = 'CHIC-' + datetime.now().strftime('%y%m%d') + '-' + uuid4().hex[:6].upper()
        created_at = datetime.now().isoformat(timespec='seconds')

        with get_db() as db:
            cur = db.execute(
                '''INSERT INTO orders
                   (order_number, created_at, customer_name, email, phone, address, city, notes, payment_method, total, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'New')''',
                (order_number, created_at, fields['customer_name'], fields['email'], fields['phone'],
                 fields['address'], fields['city'], fields['notes'], fields['payment_method'], total)
            )
            order_id = cur.lastrowid
            for item in items:
                p = item['product']
                db.execute(
                    '''INSERT INTO order_items
                       (order_id, product_slug, product_name, unit_price, quantity, subtotal)
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (order_id, p['slug'], p['name'], p['price'], item['quantity'], item['subtotal'])
                )

        line_items = '\n'.join(
            f"- {item['product']['name']} × {item['quantity']}: US${item['subtotal']:.2f}" for item in items
        )
        admin_body = f'''New Chic Interiors order\n\nOrder: {order_number}\nCustomer: {fields['customer_name']}\nEmail: {fields['email']}\nPhone: {fields['phone']}\nAddress: {fields['address']}, {fields['city']}\nPayment: {fields['payment_method']}\n\nItems:\n{line_items}\n\nTotal: US${total:.2f}\n\nNotes: {fields['notes'] or 'None'}'''
        customer_body = f'''Thank you for your Chic Interiors order.\n\nOrder: {order_number}\n\n{line_items}\n\nTotal: US${total:.2f}\nPayment method: {fields['payment_method']}\n\nOur team will contact you to confirm availability, measurements where applicable, payment and delivery/installation details.\n\nChic Interiors\n{BUSINESS['phone_display']}'''
        try:
            send_email(f'New order {order_number}', admin_body, get_setting('BUSINESS_EMAIL', BUSINESS['email']), reply_to=fields['email'])
            send_email(f'Your Chic Interiors order {order_number}', customer_body, fields['email'])
        except Exception as exc:
            app.logger.exception('Order email failed: %s', exc)

        session['cart'] = {}
        session.modified = True
        return render_template('order_success.html', order_number=order_number, total=total)

    return render_template('checkout.html', items=items, total=total, form={})


@app.route('/quote', methods=['GET', 'POST'])
def quote():
    selected_slug = request.args.get('product') or request.form.get('product')
    selected = PRODUCT_MAP.get(selected_slug) if selected_slug else None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        details = request.form.get('details', '').strip()
        product_name = PRODUCT_MAP.get(selected_slug, {}).get('name', request.form.get('product_name', '').strip())
        if not name or not email or '@' not in email or not phone or not details:
            flash('Please complete all required fields.', 'danger')
            return render_template('quote.html', selected=selected, products=PRODUCTS)
        with get_db() as db:
            db.execute(
                'INSERT INTO quotes (created_at, name, email, phone, product, details) VALUES (?, ?, ?, ?, ?, ?)',
                (datetime.now().isoformat(timespec='seconds'), name, email, phone, product_name, details)
            )
        body = f'''New quote request\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nProduct: {product_name or 'General enquiry'}\n\nDetails:\n{details}'''
        try:
            send_email('New Chic Interiors quote request', body, get_setting('BUSINESS_EMAIL', BUSINESS['email']), reply_to=email)
        except Exception as exc:
            app.logger.exception('Quote email failed: %s', exc)
        flash('Thank you. Your quote request has been received.', 'success')
        return redirect(url_for('quote'))
    return render_template('quote.html', selected=selected, products=PRODUCTS)


@app.route('/services')
def services():
    return render_template('services.html')


@app.route('/gallery')
def gallery():
    return render_template('gallery.html', products=PRODUCTS)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip() or 'Website enquiry'
        message = request.form.get('message', '').strip()
        if not name or not email or '@' not in email or not message:
            flash('Please enter your name, a valid email and a message.', 'danger')
            return render_template('contact.html')
        with get_db() as db:
            db.execute(
                'INSERT INTO messages (created_at, name, email, phone, subject, message) VALUES (?, ?, ?, ?, ?, ?)',
                (datetime.now().isoformat(timespec='seconds'), name, email, phone, subject, message)
            )
        body = f'''New website enquiry\n\nName: {name}\nEmail: {email}\nPhone: {phone or 'Not supplied'}\nSubject: {subject}\n\n{message}'''
        try:
            send_email(f'Website enquiry: {subject}', body, get_setting('BUSINESS_EMAIL', BUSINESS['email']), reply_to=email)
        except Exception as exc:
            app.logger.exception('Contact email failed: %s', exc)
        flash('Your message has been sent. We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')


def admin_required():
    if not session.get('admin_authenticated'):
        return False
    return True


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    configured = bool(get_setting('ADMIN_PASSWORD'))
    if request.method == 'POST':
        expected = get_setting('ADMIN_PASSWORD')
        if not expected:
            flash('Set ADMIN_PASSWORD in your local .env file or Cloudflare Worker secrets before using the admin dashboard.', 'warning')
        elif request.form.get('password') == expected:
            session['admin_authenticated'] = True
            return redirect(url_for('admin_orders'))
        else:
            flash('Incorrect password.', 'danger')
    return render_template('admin_login.html', configured=configured)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('home'))


@app.route('/admin/orders')
def admin_orders():
    if not admin_required():
        return redirect(url_for('admin_login'))
    with get_db() as db:
        orders = db.execute('SELECT * FROM orders ORDER BY id DESC').fetchall()
        messages = db.execute('SELECT * FROM messages ORDER BY id DESC LIMIT 20').fetchall()
        quotes = db.execute('SELECT * FROM quotes ORDER BY id DESC LIMIT 20').fetchall()
    return render_template('admin_orders.html', orders=orders, messages=messages, quotes=quotes)


@app.post('/admin/orders/<int:order_id>/status')
def admin_order_status(order_id):
    if not admin_required():
        abort(403)
    status = request.form.get('status', 'New')
    allowed = {'New', 'Confirmed', 'In Progress', 'Ready', 'Completed', 'Cancelled'}
    if status not in allowed:
        abort(400)
    with get_db() as db:
        db.execute('UPDATE orders SET status=? WHERE id=?', (status, order_id))
    flash('Order status updated.', 'success')
    return redirect(url_for('admin_orders'))


@app.errorhandler(404)
def not_found(_):
    return render_template('404.html'), 404


if not WORKER_RUNTIME:
    init_db()

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG', '1') == '1')
