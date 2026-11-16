# 🚀 Production Deployment Guide: Transport GPS Tracking System

This guide outlines step-by-step instructions for deploying the system to production across **Supabase** (Database), **Render** (Backend API), and **Vercel** (Frontend UI).

---

## 1. Cloud Infrastructure Overview

```
                      ┌────────────────────────────┐
                      │    Client Web Browsers     │
                      └─────────────┬──────────────┘
                                    │ HTTPS
                                    ▼
                      ┌────────────────────────────┐
                      │    Vercel Edge Network     │
                      │   (Frontend Static CDN)    │
                      └─────────────┬──────────────┘
                                    │ /api/v1/* (Reverse Proxy)
                                    ▼
                      ┌────────────────────────────┐
                      │       Render Cloud         │
                      │ (Flask Gunicorn Backend)   │
                      └─────────────┬──────────────┘
                                    │ TLS Pooler (Port 5432 / 6543)
                                    ▼
                      ┌────────────────────────────┐
                      │    Supabase Managed DB     │
                      │  (PostgreSQL 15+ with SSL) │
                      └────────────────────────────┘
```

---

## 2. Supabase PostgreSQL Database Setup

1. **Create Project**:
   - Log in to [Supabase](https://supabase.com) and create a new project.
   - Choose a region closest to your Render service region (e.g., `Singapore`, `Frankfurt`, or `US-East`).
2. **Retrieve Connection String**:
   - Go to **Project Settings** $\to$ **Database** $\to$ **Connection string** $\to$ Select **URI**.
   - Prefer **Session Pooler (Port 5432)** or **Direct Connection**:
     ```
     postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require
     ```
   - *Note*: Ensure special characters in your password are properly URL-encoded (e.g. `@` as `%40`).

---

## 3. Render Backend Deployment

1. **Create Web Service**:
   - Connect your GitHub repository: `https://github.com/Rohan-S96/Transport_GPS_Tracking`
   - **Environment**: `Python 3`
   - **Region**: Same geographical region as your Supabase database.
   - **Branch**: `main`

2. **Build and Start Commands**:
   - **Build Command**:
     ```bash
     pip install -r backend/requirements.txt
     ```
   - **Start Command**:
     ```bash
     gunicorn --chdir backend run:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
     ```

3. **Configure Environment Variables in Render**:
   | Variable | Value | Description |
   | :--- | :--- | :--- |
   | `DATABASE_URL` | `postgresql://...` | Full Supabase connection string |
   | `JWT_SECRET_KEY` | `[64-char-random-string]` | Cryptographic secret for signing tokens |
   | `FLASK_ENV` | `production` | Enables production security mode |
   | `ONLINE_HEARTBEAT_TIMEOUT_SECONDS` | `60` | Device inactivity timeout |
   | `PYTHON_VERSION` | `3.10.12` | Runtime version |

4. **Health Check**:
   - Set Health Check Path to: `/api/v1/health`
   - When healthy, returns `{ "status": "healthy", "database": "connected" }`.

---

## 4. Vercel Frontend Deployment

1. **Import Project**:
   - In [Vercel](https://vercel.com), select **Add New Project** $\to$ Import from GitHub.
2. **Configure Root Directory**:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Other`
3. **Verify `vercel.json` Proxy Configuration**:
   The repository includes [`vercel.json`](file:///c:/Users/Rohan/Downloads/Transport_GPS_Tracking/frontend/vercel.json) at the root and in `frontend/`:
   ```json
   {
     "rewrites": [
       {
         "source": "/api/v1/:path*",
         "destination": "https://transport-gps-tracking-backend.onrender.com/api/v1/:path*"
       }
     ]
   }
   ```
   *(Update destination URL to match your actual Render service domain).*
4. **Deploy**:
   - Every `git push origin main` triggers an automatic continuous integration build on Vercel with zero downtime.
