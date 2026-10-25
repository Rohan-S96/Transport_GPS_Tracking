# 🚚 Transport GPS Tracking & Fleet Management System

A production-grade, full-stack Transport GPS Tracking and Fleet Management platform designed for real-time fleet monitoring, geofencing, driver performance tracking, trip replay, automated alerts, and operational analytics.

---

## 🌟 Key Features

- **Real-Time GPS Tracking**: Interactive Leaflet maps with live vehicle markers, telemetry cards, and route trails.
- **Fleet & Driver Roster**: Comprehensive management of commercial vehicles, asset states, and driver assignments.
- **Geofence Management**: Polygon and circle geofence creation with breach detection and entry/exit alerts.
- **Instant Safety Alerts**: Automated triggers for overspeeding, geofence breaches, SOS, and maintenance schedules.
- **Historical Route Playback**: Step-by-step route playback with speed profiles, stops, and idle analysis.
- **Fleet Analytics & Reports**: Visual Chart.js dashboards with mileage, fuel consumption, and Excel/CSV data exports.
- **Role-Based Access Control (RBAC)**: Secure JWT token authentication supporting Fleet Managers, Dispatchers, and Drivers.

---

## 🏗️ Architecture Overview

The system is decoupled into independent frontend and backend services:

```text
[ Vercel Frontend ]
  │  HTML5 + CSS3 + Bootstrap 5 + Leaflet + Chart.js
  │  REST Client (JWT Interceptor)
  ▼
[ Railway Backend API ]
  │  Python Flask REST API + Flask-SQLAlchemy + Gunicorn
  │  Haversine Calculation + Geofencing Ray-Casting + Data Processing
  ▼
[ Supabase PostgreSQL ]
  │  Relational Database + Indexed Coordinates + Fleet History
```

### Technology Stack

| Layer | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5 | User interface and component styling |
| **Mapping** | Leaflet.js, OpenStreetMap tiles | Map rendering, markers, route polylines, geofences |
| **Visualization**| Chart.js | Fleet metrics, fuel analytics, and trip charts |
| **Hosting (Frontend)**| Vercel | High-speed global edge static hosting |
| **Backend** | Python 3.11+, Flask REST API | Business logic, API routes, telemetry processing |
| **ORM & Migrations**| Flask-SQLAlchemy, Flask-Migrate (Alembic) | Database models, schema versions, relations |
| **Security** | Flask-JWT-Extended, Werkzeug Security | Passwords hashing (bcrypt/argon2), JWT tokens |
| **Data Processing** | pandas, openpyxl | Excel/CSV report generation and telemetry aggregations |
| **WSGI Server** | Gunicorn | Production concurrent application server |
| **Hosting (Backend)**| Railway | Containerized auto-scaling backend hosting |
| **Database** | Supabase (PostgreSQL) | Managed cloud PostgreSQL database |

---

## 📂 Project Structure

```text
Transport_GPS_Tracking/
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore configuration
├── README.md                        # Master project documentation
├── API_DOCUMENTATION.md             # REST API specifications & endpoints
├── DATABASE_SCHEMA.md               # PostgreSQL schema design & relational models
├── DEPLOYMENT.md                    # Step-by-step deployment guide (Vercel + Railway + Supabase)
│
├── frontend/                        # Client-side web application (Vercel)
│   ├── vercel.json                  # Vercel routing, rewrite and security headers
│   ├── index.html                   # Fleet Operations Dashboard & KPIs
│   ├── login.html                   # User Authentication (Sign In & Register)
│   ├── live-tracking.html           # Full-screen Leaflet GPS tracking & simulator
│   ├── vehicles.html                # Fleet inventory, specs & vehicle management
│   ├── drivers.html                 # Driver roster, licenses & safety scores
│   ├── trips.html                   # Trip manifests, loaded/empty status & stops
│   ├── playback.html                # Historical route scrubber & speed replay
│   ├── companies.html               # Client companies & delivery depot sites
│   ├── geofences.html               # Geofence boundary creator & point containment
│   ├── alerts.html                  # Real-time alert feed & incident triage
│   ├── reports.html                 # Fleet analytics & Excel/CSV data exports
│   ├── users.html                   # User directory & Role-Based Access Control
│   ├── settings.html                # API connection diagnostics & user profile
│   └── assets/                      # Static resources
│       ├── css/
│       │   ├── style.css            # Master design system, dark mode, responsive layout
│       │   ├── map.css              # Custom truck pins, radar pulses, popups
│       │   └── components.css       # KPI cards, status badges, tables, modals
│       └── js/
│           ├── config.js            # Dynamic API base URL & runtime configuration
│           ├── api.js               # Centralized API fetch client with JWT interceptor & file downloader
│           ├── auth.js              # Token management, route guard & RBAC enforcement
│           ├── utils.js             # Formatting, toasts, loading states & badge helpers
│           ├── map.js               # Leaflet core engine, route history & marker manager
│           ├── dashboard.js         # KPI metrics calculation & Chart.js graphs
│           ├── live-tracking.js     # Real-time GPS poller & telemetry simulator
│           ├── vehicles.js          # Truck CRUD, driver assignments & search
│           ├── drivers.js           # Driver management & safety scoring
│           ├── trips.js             # Trip lifecycle (start/complete/cancel), cargo status & stops
│           ├── playback.js          # Interactive route timeline scrubber & replay HUD
│           ├── companies.js         # Client companies & depot locations management
│           ├── geofences.js         # Spatial geofence engine & containment checker
│           ├── alerts.js            # Safety incident monitor & acknowledgment
│           ├── reports.js           # Excel (.xlsx) and CSV report generation
│           ├── users.js             # Organization user management & role permissions
│           └── settings.js          # Live API health/readiness probe & profile editor
│
└── backend/                         # Server-side REST API (Railway)
    ├── run.py                       # Local development entrypoint
    ├── wsgi.py                      # Production WSGI application entrypoint
    ├── requirements.txt             # Python dependencies
    ├── Procfile                     # Railway worker/web process definition
    ├── runtime.txt                  # Python runtime specification
    ├── railway.json                 # Railway deployment & health check configuration
    ├── app/                         # Application package
    │   ├── __init__.py              # Application factory (create_app)
    │   ├── config.py                # Environment configs (Dev, Prod, Test)
    │   ├── extensions.py            # Extensions registry (db, migrate, jwt, cors)
    │   ├── routes/                  # REST API Blueprints
    │   │   ├── __init__.py          # Blueprint registrar
    │   │   ├── auth_routes.py       # Authentication & profile endpoints
    │   │   ├── vehicle_routes.py    # Fleet & vehicle management endpoints
    │   │   ├── tracking_routes.py   # Telemetry ingestion & spatial queries
    │   │   ├── geofence_routes.py   # Geofence creation & boundary checking
    │   │   ├── alert_routes.py      # Alert listing & acknowledgment
    │   │   ├── driver_routes.py     # Driver records & vehicle assignment
    │   │   ├── trip_routes.py       # Trip logs & historical GPS trails
    │   │   ├── maintenance_routes.py# Maintenance tickets & fuel log routes
    │   │   ├── analytics_routes.py  # Fleet analytics & Excel export endpoints
    │   │   └── health_routes.py     # Healthcheck & heartbeat ping
    │   ├── models/                  # SQLAlchemy Relational Models
    │   │   ├── __init__.py          # Models index
    │   │   ├── user.py              # User, Role, Organization models
    │   │   ├── vehicle.py           # Vehicle and tracker models
    │   │   ├── driver.py            # Driver profile model
    │   │   ├── gps_telemetry.py     # High-frequency GPS telemetry point model
    │   │   ├── geofence.py          # Geofence boundary model
    │   │   ├── alert.py             # Incident alert model
    │   │   ├── trip.py              # Vehicle trip & stop models
    │   │   └── maintenance.py       # Maintenance log & fuel record models
    │   ├── services/                # Encapsulated Business Logic
    │   │   ├── __init__.py
    │   │   ├── auth_service.py      # Auth validation & token generator
    │   │   ├── tracking_service.py  # Spatial calculations & telemetry processing
    │   │   ├── geofence_service.py  # Point-in-polygon containment engine
    │   │   ├── alert_service.py     # Rule evaluation & notification dispatch
    │   │   ├── trip_service.py      # Trip reconstruction & distance aggregation
    │   │   └── report_service.py    # Pandas data exports (Excel / CSV)
    │   ├── schemas/                 # Input Validation & Serialization
    │   │   ├── __init__.py
    │   │   ├── user_schema.py       # User payload validation
    │   │   ├── vehicle_schema.py    # Vehicle payload validation
    │   │   ├── telemetry_schema.py  # Telemetry packet validation
    │   │   ├── geofence_schema.py   # Spatial GeoJSON validation
    │   │   └── alert_schema.py      # Alert filter validation
    │   ├── utils/                   # Shared Helper Utilities
    │   │   ├── __init__.py
    │   │   ├── geo_utils.py         # Haversine distance, bearing & speed math
    │   │   ├── response_utils.py    # Standardized API response formatters
    │   │   ├── decorators.py        # RBAC and error handler decorators
    │   │   └── seed_data.py         # Initial database seeding for demo fleet
    │   └── migrations/              # Database migration repository (Alembic)
    │       ├── env.py               # Alembic migration environment
    │       ├── script.py.mako       # Migration template
    │       └── versions/            # Migration script versions
    │           └── 001_initial_schema.py
    └── tests/                       # Automated Test Suite
        ├── __init__.py
        ├── conftest.py              # Pytest fixtures & mock database
        ├── test_auth.py             # Authentication tests
        ├── test_vehicles.py         # Vehicle endpoint tests
        ├── test_tracking.py         # GPS telemetry & distance calculation tests
        └── test_geofence.py         # Geofence boundary & breach tests
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.11+
- PostgreSQL database (or free Supabase project)
- Node.js / live-server (optional for local frontend preview, or standard browser)

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a Python virtual environment
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp ../.env.example .env
# Edit .env with your Supabase PostgreSQL connection string and JWT secret

# Run database migrations
flask db upgrade

# Run local development server
python run.py
```
The API server will start at `http://127.0.0.1:5000`.

### 3. Frontend Setup & Local Development

The frontend is a modern, framework-free SPA (HTML5, Vanilla CSS3, ES6 JavaScript, Bootstrap 5, Leaflet, and Chart.js) that can run on any static web server:

#### Option A: Using Python Simple HTTP Server
```bash
# Navigate to the frontend directory
cd frontend

# Start a local static server on port 3000
python -m http.server 3000
```
Open `http://localhost:3000` in your web browser.

#### Option B: Using Node.js `serve`
```bash
cd frontend
npx serve -l 3000
```

#### Option C: VS Code / IDE Live Server
Right-click `frontend/index.html` or `frontend/login.html` and choose **"Open with Live Server"**.

#### Connecting Frontend to Backend:
- By default, `frontend/assets/js/config.js` automatically routes to `http://localhost:5000/api/v1` when running locally (`localhost` / `127.0.0.1`).
- In production, it targets the deployed Railway backend.
- You can dynamically switch or test any API endpoint live from the **Settings (`/settings.html`)** screen in the UI with instant health latency pinging.

### 4. Deploying Frontend to Vercel

```bash
# Install Vercel CLI (if not installed)
npm install -g vercel

# Deploy directly from frontend directory
cd frontend
vercel --prod
```
The preconfigured `frontend/vercel.json` ensures clean URLs, security headers, and instant routing.


---

## 🔒 Security & Best Practices

- **Zero Hardcoded Secrets**: All configuration values and credentials load from system environment variables.
- **Stateless Authentication**: Access tokens expire after a configured lifetime (default 120 mins).
- **Password Protection**: Passwords are saved exclusively as salted hashes using standard cryptographic libraries.
- **CORS Protection**: Access is restricted strictly to verified frontend origins in production.
- **SQL Injection Prevention**: All queries execute via SQLAlchemy ORM parameterized statements.

---

## 📄 License & Attribution

Designed and maintained for enterprise transport fleet management. Open-source under the MIT License.
