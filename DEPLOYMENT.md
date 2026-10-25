# 🚀 Complete Deployment Guide: Transport GPS Tracking System

This guide provides end-to-end instructions for deploying the **Transport GPS Tracking & Fleet Management System** to production:
1. **Database**: Supabase (PostgreSQL with psycopg2 driver & connection pooling)
2. **Backend**: Railway (Python Flask REST API with Gunicorn & Nixpacks)
3. **Frontend**: Vercel (Edge static delivery with HTML5, CSS3, JavaScript, Bootstrap 5, Leaflet, and Chart.js)

---

## Architecture Overview

```text
┌─────────────────────────────────┐
│     Client Browser (Web UI)     │
│   Hosted on Vercel CDN (Edge)   │
└───────────────┬─────────────────┘
                │ HTTPS REST API requests with JWT Bearer
                ▼
┌─────────────────────────────────┐
│       Railway Web Service       │
│  Flask REST API on Gunicorn     │
│   (Bound to 0.0.0.0:$PORT)      │
└───────────────┬─────────────────┘
                │ TLS Encrypted Connection (psycopg2)
                ▼
┌─────────────────────────────────┐
│       Supabase PostgreSQL       │
│     (Tables, Indexes & Views)   │
└─────────────────────────────────┘
```

---

## Part 1: Supabase PostgreSQL Setup

### 1. Create a Supabase Project
1. Log in to [Supabase](https://supabase.com).
2. Click **New Project**.
3. Choose an Organization, enter project name (e.g., `transport-gps-tracking`), and select a region closest to your Railway deployment.
4. Set a strong **Database Password** (store this securely).
5. Click **Create new project** and wait 1–2 minutes for provisioning.

### 2. Obtain Connection URI
1. In your Supabase Dashboard, go to **Project Settings** (gear icon) -> **Database**.
2. Scroll to **Connection parameters** / **Connection string**.
3. Select the **URI** tab.
4. Supabase provides two connection types:
   - **Direct Connection** (Port `5432`):
     ```text
     postgresql+psycopg2://postgres:<YOUR_DB_PASSWORD>@db.<YOUR_PROJECT_REF>.supabase.co:5432/postgres
     ```
   - **Connection Pooler (Transaction Mode)** (Port `6543` — recommended for high concurrency):
     ```text
     postgresql+psycopg2://postgres.<YOUR_PROJECT_REF>:<YOUR_DB_PASSWORD>@aws-0-<REGION>.pooler.supabase.com:6543/postgres
     ```
   *(Note: The system automatically normalizes `postgres://` or `postgresql://` schemes into `postgresql+psycopg2://` for SQLAlchemy compatibility).*

### 3. Run Database Migrations
Run the Alembic schema migrations to create all 17 tables, foreign keys, and indexes on your Supabase instance:

#### Option A: Run migrations locally against Supabase
```powershell
# From the backend directory
cd backend

# Set environment variable pointing to Supabase
$env:DATABASE_URL="postgresql+psycopg2://postgres:<YOUR_DB_PASSWORD>@db.<YOUR_PROJECT_REF>.supabase.co:5432/postgres"

# Execute Alembic migrations
flask db upgrade

# (Optional) Seed initial demo organizations, trucks, and users
flask seed-db
```

#### Option B: Run migrations via Railway CLI
```bash
# After linking your Railway project
railway run flask db upgrade
railway run flask seed-db
```

---

## Part 2: Backend Deployment on Railway

### 1. Push Repository to GitHub
Ensure all code is committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "feat: configure production deployment for Railway and Vercel"
git push origin main
```

### 2. Create Railway Service
1. Log in to [Railway](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select your `Transport_GPS_Tracking` repository.
4. Click **Deploy Now**.

### 3. Configure Service Settings
In your Railway dashboard, navigate to the service's **Settings**:
1. **Root Directory**: Set to `/backend`
   *(If left at root `/`, the included root `Procfile` and `railway.json` will automatically route to `/backend`).*
2. **Build Builder**: Leave as `NIXPACKS` (detected automatically via `backend/runtime.txt` and `backend/requirements.txt`).
3. **Start Command**:
   ```bash
   gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120
   ```
4. **Healthcheck Path**: `/api/v1/health`
5. **Healthcheck Timeout**: `100` seconds.

### 4. Configure Backend Environment Variables
In Railway, navigate to the **Variables** tab of your service and add the following required variables:

| Variable | Recommended Production Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Enables production configuration, disables debug mode, forces demo GPS mode off. |
| `PORT` | *(Provided by Railway)* | Railway automatically injects `$PORT`; Gunicorn binds to `0.0.0.0:$PORT`. |
| `SECRET_KEY` | *(Generate 32+ char random hex)* | Cryptographic session signing secret. |
| `JWT_SECRET_KEY` | *(Generate 32+ char random hex)* | Cryptographic secret for signing JWT access tokens. |
| `DATABASE_URL` | `postgresql+psycopg2://postgres:<YOUR_DB_PASSWORD>@db.<YOUR_PROJECT_REF>.supabase.co:5432/postgres` | Supabase PostgreSQL connection URI. |
| `CORS_ORIGINS` | `https://<YOUR_FRONTEND_APP>.vercel.app` | Allowed origins for browser CORS (exact Vercel domain). |
| `GPS_DEMO_MODE` | `false` | Unconditionally disabled in production to require authentic GPS telemetry. |
| `GPS_OFFLINE_TIMEOUT_SECONDS` | `600` | Inactivity window (10 min) before silent vehicles are marked offline. |
| `STOP_MINIMUM_DURATION_SECONDS`| `120` | Stationary threshold (2 min) for detecting discrete vehicle stops. |
| `STOP_RADIUS_METERS` | `50.0` | Spatial clustering radius (meters) for grouping stationary coordinates. |
| `REPORT_RETENTION_HOURS` | `168` | Retention period (7 days) for export audit log records. |

> **Security Tip**: Generate secure keys with Python:
> ```powershell
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

### 5. Generate Public Domain & Verify Health
1. Go to **Settings** -> **Networking** -> click **Generate Domain**.
2. Railway will assign a public domain, such as: `https://<YOUR_RAILWAY_APP>.up.railway.app`.
3. Open a browser or terminal and test the health endpoints:
   ```bash
   curl -s https://<YOUR_RAILWAY_APP>.up.railway.app/api/v1/health
   curl -s https://<YOUR_RAILWAY_APP>.up.railway.app/api/v1/ready
   ```
   **Expected Response**:
   ```json
   {
     "success": true,
     "status": "healthy",
     "database": "connected",
     "service": "Transport GPS Tracking API",
     "version": "1.0.0"
   }
   ```

---

## Part 3: Frontend Deployment on Vercel

The frontend is built using standard HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Leaflet, and Chart.js, requiring no Node.js compilation.

### 1. Import Project to Vercel
1. Log in to [Vercel](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Select your GitHub repository: `Transport_GPS_Tracking`.

### 2. Configure Vercel Project Settings
In the **Configure Project** screen:
1. **Framework Preset**: Select **Other**.
2. **Root Directory**: Click *Edit* and select **`frontend`**.
3. **Build and Output Settings**:
   - Build Command: *None (Leave disabled / empty)*
   - Output Directory: *None (Leave disabled / empty)*
4. Click **Deploy**.

### 3. Configure Frontend API URL
Because the frontend is static HTML/JavaScript, the API base URL is resolved via the public configuration in [`frontend/assets/js/config.js`](file:///c:/Users/Rohan/Downloads/Transport_GPS_Tracking/frontend/assets/js/config.js):

1. Open [`frontend/assets/js/config.js`](file:///c:/Users/Rohan/Downloads/Transport_GPS_Tracking/frontend/assets/js/config.js) in your repository:
   ```javascript
   const PUBLIC_CONFIG = {
     // Replace this placeholder with your deployed Railway service URL:
     PRODUCTION_API_URL: 'https://<YOUR_RAILWAY_APP>.up.railway.app/api/v1',
     LOCAL_API_URL: 'http://localhost:5000/api/v1',
     POLL_INTERVAL_MS: 4000,
     MAP_DEFAULT_CENTER: [19.0760, 72.8777],
     MAP_DEFAULT_ZOOM: 11
   };
   ```
2. Replace `'https://<YOUR_RAILWAY_APP>.up.railway.app/api/v1'` with your actual Railway public domain URL.
3. Commit and push to GitHub:
   ```bash
   git commit -am "chore: set production API URL in config.js"
   git push origin main
   ```
   *Vercel will automatically redeploy the new commit within seconds.*

### 4. Alternative Runtime Override (No Redeployment Needed)
Testers and administrators can also point the frontend to any backend URL on the fly:
1. Open your deployed Vercel site in a browser.
2. Navigate to **System Settings** (`/settings.html`).
3. Under **Runtime API Endpoint URL**, enter your Railway URL and click **Save & Test**.
4. The frontend verifies connectivity live using `/api/v1/health` and `/api/v1/ready` and stores your preference in browser `localStorage`.

### 5. Update CORS in Railway
Once Vercel assigns your production URL (e.g., `https://<YOUR_FRONTEND_APP>.vercel.app`):
1. Go back to Railway -> **Variables**.
2. Update `CORS_ORIGINS`:
   ```env
   CORS_ORIGINS=https://<YOUR_FRONTEND_APP>.vercel.app
   ```
3. Railway will restart the container with the updated CORS policy.

---

## Part 4: Excel & CSV Report Downloads Security

- **Authentication & RBAC**: The `/api/v1/analytics/export` endpoint requires a valid JWT token with at least `fleet_manager` or `admin` role. Unauthorized requests receive `401 Unauthorized` or `403 Forbidden`.
- **In-Memory Streaming**: Reports are generated using `pandas` and `openpyxl` directly into an in-memory `io.BytesIO` buffer. No files are persisted to server local disk, ensuring zero risk of temporary file leakage or container disk exhaustion.
- **Tenant Isolation**: When generating reports, the user's `organization_id` is extracted from the JWT token claims, ensuring users can only export data belonging to their own organization.

---

## Part 5: Pre-Flight Production Checklist

Before going live with commercial fleet tracking, complete this checklist:

- [ ] **Database Connectivity**: `GET https://<YOUR_RAILWAY_APP>.up.railway.app/api/v1/ready` returns `200 OK` with `status: "ready"`.
- [ ] **No Default Secrets**: Verify `SECRET_KEY` and `JWT_SECRET_KEY` in Railway are at least 32 characters long and not set to dev default values.
- [ ] **No Localhost URLs in Production**: Confirm [`frontend/assets/js/config.js`](file:///c:/Users/Rohan/Downloads/Transport_GPS_Tracking/frontend/assets/js/config.js) points to your live Railway domain.
- [ ] **Production GPS Demo Mode Off**: Verify `GPS_DEMO_MODE=false` in Railway variables.
- [ ] **CORS Restricted**: Test making a fetch request from an unauthorized domain; verify that the browser blocks the response.
- [ ] **Login Flow**: Log in with demo admin credentials (`admin@swifttransport.com` / `Admin@12345`), verify JWT token is stored, and change the default admin password from the settings page.
- [ ] **Excel Report Export**: Navigate to **Reports & Export** (`/reports.html`) and test downloading both Excel (`.xlsx`) and CSV reports.
- [ ] **Live Telemetry & Geofencing**: Check that OpenStreetMap tiles load on the map without mixed-content (HTTP/HTTPS) warnings.
