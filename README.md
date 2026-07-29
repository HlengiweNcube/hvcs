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

When prompted, set the role to `ADMIN` or update it via the admin panel at `/admin/`.

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

