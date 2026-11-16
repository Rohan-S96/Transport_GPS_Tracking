# 🚚 Transport GPS Tracking & Fleet Management Documentation

Welcome to the comprehensive documentation suite for the **Transport GPS Tracking & Fleet Telemetry System**. This repository houses the entire technical specification, architecture, REST API reference, database schema, driver mobile tracker guide, developer workflows, and deployment procedures.

---

## 📚 Documentation Index

| Document | Description |
| :--- | :--- |
| [**1. Project Overview**](./PROJECT_OVERVIEW.md) | High-level system goals, features, technology stack, and user roles. |
| [**2. System Architecture**](./ARCHITECTURE.md) | Backend service layers, real-time GPS processing pipeline, frontend architecture, and Mermaid sequence diagrams. |
| [**3. REST API Reference**](./API_DOCUMENTATION.md) | Complete documentation of all endpoints, request/response formats, authentication, and error codes. |
| [**4. Database Schema**](./DATABASE_SCHEMA.md) | Entity-Relationship (ER) diagram, table structures, foreign keys, indexes, and PostgreSQL/SQLite setup. |
| [**5. Mobile GPS Tracker Guide**](./MOBILE_TRACKER.md) | Technical architecture of the driver smartphone GPS tracker (WakeLock, Battery API, online/offline lifecycle). |
| [**6. Deployment Guide**](./DEPLOYMENT_GUIDE.md) | Step-by-step production deployment for Render (Backend), Vercel (Frontend), and Supabase (PostgreSQL). |
| [**7. Developer & Operations Guide**](./DEVELOPER_GUIDE.md) | Local environment setup, test suite execution (`pytest`), seeding sample data, and troubleshooting. |

---

## ⚡ Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
Backend runs at `http://localhost:5000` (API prefix: `/api/v1`).

### 2. Frontend Setup
Open `frontend/index.html` or serve with any static web server:
```bash
cd frontend
python -m http.server 3000
```
Open `http://localhost:3000` in your web browser.

### 3. Run Automated Tests
```bash
python -m pytest backend/tests
```
All 20 unit and integration tests validate authentication, GPS telemetry, geofence collision detection, vehicle online/offline synchronization, and analytics.

---

## 🏢 Platform Features At A Glance

- **Live Fleet Radar**: Real-time Leaflet map with automatic 5–10s polling, vehicle clustering, rotation heading icons, and live status cards.
- **Instant Online / Offline Detection**: Real-time heartbeat detection ensuring mobile and hardware trackers reflect online/offline state across both the live radar and the fleet inventory table.
- **Driver Smartphone GPS Tracking**: Native browser tracker (`driver-tracker.html`) utilizing HTML5 Geolocation, Screen WakeLock, Battery API, and offline queueing.
- **Geofence Engine**: Ray-casting point-in-polygon algorithm and Haversine radius calculations for automated entry/exit incident detection.
- **Route Historical Playback**: Animated timeline scrubbing, speed profiling, and stop duration detection.
- **Multi-Tenant Architecture**: Organization-scoped data isolation with Role-Based Access Control (Admin, Fleet Manager, Dispatcher, Driver, Viewer).
- **Persistent Theme Toggle**: Seamless dark and light themes with persistence across browser tabs.
