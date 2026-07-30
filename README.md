# HVCS — Home Visit Care System

A web application for managing home care visits, caregivers, clients, and compliance reporting.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.6, Django REST Framework |
| Auth | JWT (SimpleJWT) |
| Database | SQLite (development) |
| Frontend A | Django Templates + CSS |
| Frontend B | React 18 + Vite (SPA) |

---

## Project Structure

```
hvcs/
├── accounts/          # Django app — models, views, API views
├── hvcs_project/      # Django settings and root URLs
├── templates/         # Django HTML templates (Frontend A)
├── frontend/          # React/Vite app (Frontend B)
├── manage.py
└── requirements.txt
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- pip

---

## Setup

### 1. Clone / unzip the project

```bash
cd hvcs
```

### 2. Create and activate a Python virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Create a superuser (Admin account)

```bash
python manage.py createsuperuser
```

Django will prompt for a username, email, and password and write the record directly to the database — no browser required. The `ensure_superuser` management command (used on Render) does the same thing from environment variables and sets `role = ADMIN` automatically.

This is the only way to create an Admin account and is intentional — admin accounts are provisioned by a system administrator at the command line, not through the web UI. This is a Django security best practice: it prevents anyone from self-registering as an administrator through a web form.

Once the admin account exists, all subsequent Managers and Caregivers are created through the web interface by the logged-in admin at `/accounts/managers/add/` and `/accounts/caregivers/add/`.

### 6. Install React dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Running the Application

You need **two terminals** running simultaneously.

### Terminal 1 — Django backend

```bash
# From the project root
python manage.py runserver
```

Runs at: `http://127.0.0.1:8000/`

### Terminal 2 — React frontend (Vite dev server)

```bash
cd frontend
npm run dev
```

Runs at: `http://localhost:5173/`

---

## Accessing the App

### Django Template System (Frontend A)
> `http://127.0.0.1:8000/`

The original HTML-based frontend. Login with your superuser credentials.

### React SPA (Frontend B)
> `http://localhost:5173/react/login`

A modern single-page app consuming the REST API. Login with the same credentials.

---

## User Roles

| Role | Access |
|---|---|
| **ADMIN** | Full access — manage caregivers, clients, visits, compliance |
| **MANAGER** | View visits and compliance reports |
| **CAREGIVER** | View own visits and check in/out |

---

## Key Features

- Role-based access control (Admin / Manager / Caregiver)
- Caregiver management (create, edit, delete)
- Client management
- Visit scheduling and status tracking
- GPS check-in for caregivers
- Compliance dashboard with visit statistics and alerts
- REST API with JWT authentication
- React SPA frontend

---

## REST API

Base URL: `http://127.0.0.1:8000/api/v1/`

| Endpoint | Description |
|---|---|
| `POST /auth/login/` | Obtain JWT access + refresh tokens |
| `GET /auth/me/` | Get current user profile |
| `POST /auth/register/` | Register a new caregiver |
| `GET /clients/` | List clients |
| `GET /caregivers/` | List caregivers |
| `GET /visits/` | List visits |
| `GET /dashboard/admin/` | Admin dashboard stats |
| `GET /dashboard/manager/` | Manager dashboard stats |
| `GET /dashboard/caregiver/` | Caregiver dashboard stats |

---

## Environment Variables (optional)

Create a `.env` file in the project root to override defaults:

```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Running the Tests

```bash
python manage.py test accounts
```

41 automated tests covering authentication, CRUD operations, GPS check-in/out, reverse geocoding, compliance reporting, and the CSV audit export.

---

## Security

This project follows OWASP secure-by-default practices. The key controls are documented below.

### Authentication & Passwords

| Control | Implementation |
|---|---|
| Password hashing | Django's PBKDF2-SHA256 with a random salt (built-in `AUTH_PASSWORD_HASHERS`) |
| Session auth | Django session middleware with `HttpOnly` cookies |
| API auth | JWT access + refresh tokens via `djangorestframework-simplejwt`; tokens are short-lived |
| Brute-force mitigation | Django's `django.contrib.auth` raises `PermissionDenied` on failed login; lockout can be added via `django-axes` |

### Authorisation (Access Control)

| Control | Implementation |
|---|---|
| Role-based access control | Custom `Role` field on `User` model (`ADMIN`, `MANAGER`, `CAREGIVER`) |
| View-level enforcement | `@login_required` + `@role_required(...)` decorators on every protected view |
| API-level enforcement | `IsAuthenticated` permission class; role checked inside each API view |
| Object-level isolation | Caregivers can only access their own visits and clients — queries filtered by `request.user` |

### Injection Prevention

| Control | Implementation |
|---|---|
| SQL injection | Django ORM used throughout — no raw SQL queries; parameterised queries only |
| XSS | Django template engine auto-escapes all user-supplied values by default |
| Command injection | No shell commands or `subprocess` calls; external API called via `urllib.request` with a fixed URL |

### CSRF Protection

All HTML forms include `{% csrf_token %}`. Django's `CsrfViewMiddleware` rejects any POST/PUT/DELETE request without a valid token. The React SPA uses JWT (stateless) and does not rely on cookies, so CSRF is not applicable there.

### Sensitive Data

| Control | Implementation |
|---|---|
| `SECRET_KEY` | Read from `SECRET_KEY` environment variable; never hard-coded |
| `DEBUG` mode | `DEBUG = os.getenv('DEBUG', 'False') == 'True'` — defaults to `False` in production |
| Database credentials | Managed by Render; passed in via `DATABASE_URL` environment variable |
| GPS coordinates | Stored in the database; only shown to the caregiver who made the check-in and to Admin/Manager roles |

### Transport Security

The application is deployed on **Render** which enforces HTTPS for all requests. HTTP traffic is automatically redirected to HTTPS at the platform level.

### Security Headers

Django's `SecurityMiddleware` (enabled by default) sets:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY` (via `X_FRAME_OPTIONS = 'DENY'` default)

WhiteNoise serves static files with cache headers but without exposing directory listings.

### Third-Party API

The reverse-geocoding call to OpenStreetMap Nominatim:
- Is made **server-side** — the client never receives the raw API request
- Uses a descriptive `User-Agent` header as required by Nominatim's usage policy
- Fails silently on error (returns empty string) — no user data is leaked in an exception

---

## Database Design

### Entity-Relationship Overview

```
User (Django built-in + custom Role field)
 └─── Caregiver (OneToOne → User)
 └─── [Manager/Admin users have no separate profile table]

Caregiver ──── Visit ──── Client
```

Four tables drive the application:

| Model | Key fields | Notes |
|---|---|---|
| `User` | `id`, `username`, `email`, `role` (ADMIN/MANAGER/CAREGIVER) | Extends `AbstractUser`; role gates every view |
| `Caregiver` | `id`, `user` (OneToOne), `first_name`, `last_name`, `phone`, `qualifications`, `employment_status`, `date_left`, `is_active` | Separate profile so admin/manager users don't need one; never hard-deleted (see below) |
| `Client` | `id`, `first_name`, `last_name`, `address`, `contact_phone`, `care_needs`, `is_active` | Soft-deletable via `is_active` flag |
| `Visit` | `id`, `caregiver` (FK), `client` (FK), `scheduled_date`, `scheduled_time`, `status`, `notes`, `check_in_time`, `check_out_time`, `check_in_lat`, `check_in_lng`, `check_in_address` | GPS data stored on check-in |

### Caregiver Soft-Delete & Employment Status

Caregivers are **never hard-deleted**. Deleting a caregiver record would orphan all their visit history and destroy the compliance audit trail. Instead, when a caregiver resigns or is terminated:

1. `caregiver.is_active` is set to `False` — they no longer appear in active lists or receive new visits
2. `caregiver.employment_status` is set to `RESIGNED` or `TERMINATED`
3. `caregiver.date_left` records when they left
4. `caregiver.user.is_active` is set to `False` — their login is disabled

Their visit records remain fully intact and visible in compliance and audit reports.

`EmploymentStatus` choices: `ACTIVE` | `RESIGNED` | `TERMINATED`

### POPIA Compliance (Protection of Personal Information Act)

South African law (POPIA) grants individuals the **right to request erasure** of their personal data. The `Caregiver.anonymize()` method satisfies this without destroying the operational record:

```python
def anonymize(self):
    self.first_name = 'Anonymised'
    self.last_name  = f'User {self.pk}'   # preserves the PK link to visit records
    self.phone = ''
    self.qualifications = ''
    self.profile_image = None
    self.user.email = self.user.first_name = self.user.last_name = ''
    self.user.is_active = False
```

- **Personal identifiers erased**: name, phone, email, profile photo, qualifications
- **Preserved**: `caregiver.id`, all linked `Visit` rows (required for legal/audit purposes)
- The "Anonymise & Deactivate" button on the deactivate confirmation page triggers this method

`Visit.status` uses an inner `TextChoices` enum: `SCHEDULED → IN_PROGRESS → COMPLETED` (or `CANCELLED`).

All relationships use Django's ORM `ForeignKey` / `OneToOneField` with `on_delete=CASCADE`, so deleting a `User` cascades to their `Caregiver` record and all associated `Visit` rows.

Full field definitions: [accounts/models.py](accounts/models.py)

### Design Evolution

The original ERD included two additional tables — `VISIT_NOTE` and `COMPLIANCE_ALERT` — that were consolidated during implementation:

| Planned table | Why it was removed | What replaced it |
|---|---|---|
| `VISIT_NOTE` | Each visit requires only a single note; a separate table adds a join with no benefit at this scale | `Visit.notes` text field — stores the note directly on the visit record |
| `COMPLIANCE_ALERT` | Stored alerts go stale the moment a caregiver checks in; real-time accuracy is more important than persistence | Computed live in `admin_dashboard_view` and `compliance_dashboard` — missed check-ins and never-started visits are derived from `Visit.status` on every page load |

The four-table schema demonstrates all required relationship types:

| Relationship | Tables involved | Django field |
|---|---|---|
| One-to-One | `Caregiver` → `User` | `OneToOneField(User, on_delete=CASCADE)` |
| Many-to-One (FK) | `Visit` → `Caregiver` | `ForeignKey(Caregiver, on_delete=CASCADE)` |
| Many-to-One (FK) | `Visit` → `Client` | `ForeignKey(Client, on_delete=CASCADE)` |
| Cascade delete | `User` → `Caregiver` → `Visit` | `on_delete=CASCADE` on both FKs |

---

## settings.py Walkthrough

| Setting | How it is read | Purpose |
|---|---|---|
| `SECRET_KEY` | `os.getenv('SECRET_KEY', '<dev-fallback>')` | Django signing key; always overridden in production via Render env var |
| `DEBUG` | `os.getenv('DEBUG', 'False') == 'True'` | Defaults `False`; set `DEBUG=True` locally via `.env` |
| `ALLOWED_HOSTS` | `os.getenv('ALLOWED_HOSTS', 'localhost').split(',')` | Comma-separated list injected by Render |
| `DATABASES` | `dj_database_url.parse(os.getenv('DATABASE_URL'))` with SQLite fallback | Render injects `DATABASE_URL`; local dev uses SQLite |
| `STATIC_ROOT` | `BASE_DIR / 'staticfiles'` | WhiteNoise collects here on deploy |
| `STATICFILES_STORAGE` | `whitenoise.storage.CompressedStaticFilesStorage` | Serves compressed, cache-busted static files |
| `INSTALLED_APPS` | Includes `accounts`, `rest_framework`, `corsheaders` | Core app + API + cross-origin support for React dev server |
| `AUTH_USER_MODEL` | `'accounts.User'` | Points Django at the custom user model |

### Local .env example

Create `.env` in the project root (never commit it):

```
SECRET_KEY=replace-me-with-50-random-chars
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

`python-dotenv` is not a dependency; you can set the variables in your shell or use `export` / PowerShell `$env:`.

---

## PostgreSQL Setup (local)

The project uses **SQLite for local development** and **PostgreSQL on Render**. To run locally against PostgreSQL:

1. Create a database and user:

```sql
CREATE DATABASE hvcs_dev;
CREATE USER hvcs_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE hvcs_dev TO hvcs_user;
```

2. Export the `DATABASE_URL` before running Django:

```bash
export DATABASE_URL="postgres://hvcs_user:yourpassword@localhost:5432/hvcs_dev"
```

3. Run migrations and create the superuser as usual:

```bash
python manage.py migrate
python manage.py createsuperuser
```

The `dj-database-url` package in `requirements.txt` translates `DATABASE_URL` into Django's `DATABASES` dict automatically.

### PostgreSQL and the test suite

Django creates a temporary `test_hvcs_dev` database when running tests. The `hvcs_user` role needs `CREATEDB` privileges:

```sql
ALTER USER hvcs_user CREATEDB;
```

---

## URL / Endpoint Overview

### Django Template URLs (`/accounts/`)

| URL pattern | View | Role required |
|---|---|---|
| `/` | `landing` | Public |
| `/accounts/register/` | `register` | Public |
| `/accounts/caregiver-dashboard/` | `caregiver_dashboard` | CAREGIVER |
| `/accounts/manager-dashboard/` | `manager_dashboard` | MANAGER |
| `/accounts/admin-dashboard/` | `admin_dashboard` | ADMIN |
| `/accounts/caregivers/` | `caregiver_list` | ADMIN |
| `/accounts/caregivers/add/` | `caregiver_create` | ADMIN |
| `/accounts/caregivers/<pk>/edit/` | `caregiver_update` | ADMIN |
| `/accounts/caregivers/<pk>/delete/` | `caregiver_delete` | ADMIN |
| `/accounts/clients/` | `client_list` | ADMIN |
| `/accounts/clients/add/` | `client_create` | ADMIN |
| `/accounts/clients/<pk>/edit/` | `client_update` | ADMIN |
| `/accounts/clients/<pk>/delete/` | `client_delete` | ADMIN |
| `/accounts/visits/` | `visit_list` | ADMIN |
| `/accounts/visits/add/` | `visit_create` | ADMIN |
| `/accounts/visits/<pk>/delete/` | `visit_delete` | ADMIN |
| `/accounts/compliance/` | `compliance_dashboard` | ADMIN/MANAGER |
| `/accounts/my-visits/` | `caregiver_my_visits` | CAREGIVER |
| `/accounts/my-clients/` | `caregiver_my_clients` | CAREGIVER |
| `/accounts/my-profile/` | `caregiver_my_profile` | CAREGIVER |
| `/accounts/visits/<pk>/checkin/` | `caregiver_checkin` | CAREGIVER |
| `/accounts/visits/<pk>/checkout/` | `caregiver_checkout` | CAREGIVER |

### REST API URLs (`/api/v1/`)

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/v1/auth/login/` | POST | None | Returns JWT access + refresh tokens |
| `/api/v1/auth/refresh/` | POST | Refresh token | Rotates access token |
| `/api/v1/auth/me/` | GET | JWT | Returns logged-in user profile |
| `/api/v1/auth/register/` | POST | None | Creates caregiver account |
| `/api/v1/clients/` | GET | JWT | Lists all active clients |
| `/api/v1/caregivers/` | GET | JWT | Lists all active caregivers |
| `/api/v1/visits/` | GET | JWT | Lists visits (filtered by role) |
| `/api/v1/dashboard/admin/` | GET | JWT + ADMIN | Admin stats for React SPA |
| `/api/v1/dashboard/manager/` | GET | JWT + MANAGER | Manager stats for React SPA |
| `/api/v1/dashboard/caregiver/` | GET | JWT + CAREGIVER | Caregiver stats for React SPA |

### Architecture note

All business logic lives in `accounts/views.py` (template views) and `accounts/api_views.py` (DRF views). URLs are wired in `accounts/urls.py` and `accounts/api_urls.py` respectively and included from `hvcs_project/urls.py`. This keeps the root URL config minimal.

---

## Authentication & Authorisation in Depth

### How it works (Django template frontend)

1. The user submits their credentials to `/accounts/login/` (Django's built-in `LoginView`).
2. Django verifies the password with PBKDF2-SHA256, creates a session, and sets an `HttpOnly` session cookie.
3. Every subsequent request carries the cookie; Django middleware restores `request.user`.
4. Protected views are decorated with `@login_required` (redirects to login if anonymous) and `@role_required(Role.X)` (returns 403 if the wrong role).

### The `@role_required` decorator

```python
# accounts/decorators.py
def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator
```

Roles are checked at the view level; Django's built-in `PermissionDenied` returns a 403 response.

### How it works (React SPA)

1. React POSTs credentials to `/api/v1/auth/login/`, receives `access` and `refresh` JWT tokens.
2. `access` token is stored in `localStorage`; attached as `Authorization: Bearer <token>` on every API request.
3. API views use `IsAuthenticated` + manual role checks:

```python
class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.ADMIN:
            return Response(status=403)
        ...
```

---

## Test Design Walkthrough

The test suite lives in [accounts/tests.py](accounts/tests.py) and contains **41 tests** across 8 test classes.

### Test classes

| Class | What it tests |
|---|---|
| `AuthTests` | Login/logout flows, role-based redirect after login |
| `RegistrationTests` | Self-registration creates User + Caregiver; auto-login on success |
| `ClientCRUDTests` | Admin can list, create, update, delete clients |
| `VisitCRUDTests` | Admin can list, filter, create, delete visits |
| `CheckInOutTests` | Caregiver can check in (with/without GPS); check out marks COMPLETED |
| `CaregiverDashboardTests` | Caregiver sees own visits; cannot access admin views |
| `ComplianceTests` | Compliance % calculation; filter by caregiver; CSV export header |
| `ReverseGeocodeTests` | `reverse_geocode()` returns address string; handles network errors |

### Example: GPS check-in test

```python
def test_checkin_without_gps(self):
    self.client.login(username='caregiver', password='pass')
    response = self.client.post(
        f'/accounts/visits/{self.visit.pk}/checkin/',
        {},  # no lat/lng
    )
    self.assertRedirects(response, f'/accounts/visits/{self.visit.pk}/')
    self.visit.refresh_from_db()
    self.assertEqual(self.visit.status, Visit.Status.IN_PROGRESS)
    self.assertIsNotNone(self.visit.check_in_time)
```

This verifies that:
- A POST without coordinates still advances status to `IN_PROGRESS`
- `check_in_time` is recorded even without GPS data
- The view redirects to the visit detail page

### Test isolation

Each test class uses Django's `TestCase` which wraps every test in a database transaction that is rolled back after the test — no leftover data between tests. Helper functions (`make_admin`, `make_caregiver_user`, `make_client`, `make_visit`) create the minimum required fixtures inline.

---

## Why Function-Based Views?

This project uses **function-based views (FBVs)** throughout `accounts/views.py`. The key reasons:

1. **Aggregation logic**: Dashboard views combine data from 3–4 models with filtering, alert computation, and compliance calculations. This logic does not map onto a single `queryset` attribute of a class-based view.
2. **Clarity for assessment**: FBVs make the request → process → response flow explicit and linear, which is easier to follow and test.
3. **Decorator composition**: `@role_required` + `@login_required` compose cleanly on plain functions.

Where CBVs would be appropriate (if the project were extended):
- `ClientListView(ListView)` — pure list with no aggregation
- `ClientCreateView(CreateView)` — standard model form with no custom logic
- `VisitDetailView(DetailView)` — single-object display

Django's `LoginView` (a CBV) is already used for the login page.

---

## Deployment on Render

### Environment variables (set in Render dashboard)

| Variable | Value |
|---|---|
| `SECRET_KEY` | A 50-character random string |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `yourhostname.onrender.com` |
| `DATABASE_URL` | Auto-injected by Render PostgreSQL add-on |

### Deployment sequence

1. Push code to `main` branch.
2. Render detects the push and runs the **build command**:
   ```
   pip install -r requirements.txt && python manage.py collectstatic --noinput
   ```
3. Render runs the **start command**:
   ```
   gunicorn hvcs_project.wsgi:application
   ```
4. On first deploy, run migrations manually from the Render shell:
   ```
   python manage.py migrate
   python manage.py ensure_superuser
   ```

> **Note**: Migrations must be run **after** `DATABASE_URL` is set and the PostgreSQL instance is provisioned. Running `migrate` before the database is ready will fail.

The `ensure_superuser` management command creates the initial admin user from `DJANGO_SUPERUSER_*` environment variables so the first login does not require shell access.

---

## Configuration Reference

All runtime behaviour is controlled through environment variables read in `hvcs_project/settings.py`. No values are hard-coded except safe development defaults.

### Environment Variables

| Variable | Default | Required in production | Description |
|---|---|---|---|
| `SECRET_KEY` | insecure dev string | **Yes** | Django signing key — must be a random 50-character string in production |
| `DEBUG` | `True` | **Yes** (`False`) | Enables Django debug mode; must be `False` in production |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | **Yes** | Comma-separated list of hostnames Django will serve; Render's hostname is appended automatically via `RENDER_EXTERNAL_HOSTNAME` |
| `DATABASE_URL` | SQLite fallback | **Yes** | Full DSN for the database; Render injects this automatically from the linked PostgreSQL add-on |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | No | Comma-separated list of origins allowed to call the REST API from a browser (React dev server in development) |
| `EMAIL_BACKEND` | console backend | No | Set to `django.core.mail.backends.smtp.EmailBackend` to send real emails |
| `EMAIL_HOST` | `smtp.gmail.com` | No | SMTP server hostname |
| `EMAIL_PORT` | `587` | No | SMTP port |
| `EMAIL_USE_TLS` | `True` | No | Enable STARTTLS for the SMTP connection |
| `EMAIL_HOST_USER` | _(empty)_ | No | SMTP login username |
| `EMAIL_HOST_PASSWORD` | _(empty)_ | No | SMTP login password |
| `DEFAULT_FROM_EMAIL` | `noreply@hvcs.local` | No | Sender address for all outgoing emails |
| `DJANGO_SUPERUSER_USERNAME` | _(empty)_ | No | Used by `ensure_superuser` to create the first admin account on deploy |
| `DJANGO_SUPERUSER_PASSWORD` | _(empty)_ | No | Password for the auto-created superuser |
| `DJANGO_SUPERUSER_EMAIL` | _(empty)_ | No | Email for the auto-created superuser |

### Database Configuration

`settings.py` checks for `DATABASE_URL` at startup:

```python
database_url = os.getenv('DATABASE_URL')
if database_url:
    DATABASES = {'default': dj_database_url.parse(database_url, conn_max_age=600)}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
```

- **Local development** — SQLite file at `db.sqlite3` (no setup needed)
- **Production (Render)** — PostgreSQL via `DATABASE_URL`; SSL is enforced automatically when the URL starts with `postgres://`
- `conn_max_age=600` keeps database connections alive for 10 minutes (connection pooling)

### Django REST Framework

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # React SPA
        'rest_framework.authentication.SessionAuthentication',         # Django template AJAX
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}
```

Two authentication backends are active simultaneously:
- **JWTAuthentication** — used by the React SPA; the client sends `Authorization: Bearer <token>`
- **SessionAuthentication** — used by Django template pages that make AJAX calls to the API (e.g., the live alert badge on the admin dashboard)

### JWT Token Settings

```python
SIMPLEJWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

| Setting | Value | Reason |
|---|---|---|
| `ACCESS_TOKEN_LIFETIME` | 8 hours | Long enough for a full working shift without re-login |
| `REFRESH_TOKEN_LIFETIME` | 7 days | Allows background token rotation without forcing weekly re-login |
| `AUTH_HEADER_TYPES` | `Bearer` | Standard OAuth2 header format |

### CORS Configuration

```python
CORS_ALLOWED_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']
CORS_ALLOW_CREDENTIALS = True
```

CORS is only needed during development when the React dev server (port 5173) calls the Django API (port 8000). In production on Render both are served from the same origin so CORS headers are not required.

Override for a custom domain:
```
CORS_ALLOWED_ORIGINS=https://myapp.onrender.com,https://myotherdomain.com
```

### Static Files (WhiteNoise)

```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

WhiteNoise serves static files directly from the Django process without a separate web server:
- `CompressedStaticFilesStorage` — pre-compresses files with gzip at build time; does not rename already-hashed Vite filenames
- `STATIC_ROOT` — `collectstatic` copies all static files here before deployment
- The React/Vite production build (`frontend/dist/`) is included in `STATICFILES_DIRS` so `collectstatic` picks up the hashed JS/CSS bundles automatically

### Email Configuration

The default `console` backend prints emails to stdout (useful for local development to test password-reset flows without a real mail server).

To enable real email in production, set these environment variables:

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Middleware Order

The middleware stack is order-sensitive:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',      # HTTPS redirect, security headers
    'whitenoise.middleware.WhiteNoiseMiddleware',          # static files — must be after SecurityMiddleware
    'corsheaders.middleware.CorsMiddleware',               # CORS headers — must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

`SecurityMiddleware` is first so HTTPS redirects and security headers are applied before any other processing. `CorsMiddleware` must appear before `CommonMiddleware` so preflight `OPTIONS` requests are handled before Django's URL routing rejects them.

### Django Admin Panel

All four models are registered in `accounts/admin.py` and accessible at `/admin/`:

| Admin URL | Model | Columns shown |
|---|---|---|
| `/admin/accounts/user/` | `User` | `id`, `username`, `email`, `role`, `is_active` |
| `/admin/accounts/caregiver/` | `Caregiver` | `id`, `first_name`, `last_name`, `user` (FK → User), `phone`, `is_active` |
| `/admin/accounts/client/` | `Client` | `id`, `first_name`, `last_name`, `contact_phone`, `is_active` |
| `/admin/accounts/visit/` | `Visit` | `id`, `caregiver` (FK → Caregiver), `client` (FK → Client), `scheduled_date`, `scheduled_time`, `status` |

The Visit admin list is the clearest demonstration of the foreign-key joins: the `caregiver` and `client` columns each resolve their FK to display the related record's name in a single list view.

Access requires a user with `is_staff = True` (all Admin-role users qualify).


