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
