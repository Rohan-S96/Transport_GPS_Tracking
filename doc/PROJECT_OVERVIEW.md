# 🌐 Project Overview: Transport GPS Tracking System

## 1. Executive Summary

The **Transport GPS Tracking & Fleet Management System** is an enterprise-grade telemetry, dispatch, and logistics intelligence platform. It bridges the gap between commercial fleet operations, real-time vehicle telematics, and driver tracking.

The system supports both dedicated hardware IoT GPS trackers (via standard IMEI packets) and smartphone-based driver tracking (via modern web APIs), eliminating the prohibitive upfront hardware costs for small to mid-sized transport carriers.

---

## 2. Core Capabilities

### 📡 Real-Time Fleet Visibility
- **Live Fleet Radar**: Interactive Leaflet.js map tracking all vehicles with smooth marker transitions, vehicle heading rotation, speed badges, and live connection status.
- **Instant Online / Offline Sync**: 10-second rapid heartbeat check accurately tracks device power, tab closures, and cellular dropouts.
- **Public Vehicle Roster**: Lightweight endpoint enabling drivers to pair their smartphone with any fleet vehicle instantly without administrative overhead.

### 🗺️ Geofencing & Spatial Intelligence
- **Polygon & Circular Geofences**: Draw custom depot boundaries, customer delivery zones, and hazardous corridors directly on the map.
- **Automated Incident Alerts**: Ray-casting point-in-polygon and Haversine distance algorithms trigger instant alerts when vehicles enter or exit designated areas.
- **Overspeed Detection**: Dynamic speed limit verification against vehicle and organization safety thresholds.

### 📱 Driver Smartphone Web Tracker
- **No App Installation Required**: Runs directly in mobile Safari, Chrome, and Firefox browsers.
- **Screen WakeLock API**: Keeps smartphone displays illuminated during navigation to prevent background throttling.
- **Battery Status Telemetry**: Reports driver phone battery percentage and charging state directly to dispatchers.
- **Offline Resilient Queue**: Automatically stores GPS coordinates in LocalStorage when entering cell dead-zones and bulk-synchronizes upon signal recovery.

### 📊 Route Playback & Analytics
- **Historical Trail Scrubbing**: Step through past trips second-by-second with interactive time scrubbers, speed profiles, and idle duration markers.
- **Fleet KPI Dashboard**: High-level metrics on active vehicles, fleet utilization, average speeds, fuel burn, and open safety incidents.
- **Exportable Reports**: Generate Excel/CSV reports for mileage audits, trip logs, and driver hours.

---

## 3. Technology Stack

### Backend
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **Python** | 3.10+ | Core application runtime |
| **Flask** | 3.0+ | Lightweight WSGI micro-framework |
| **SQLAlchemy** | 2.0+ | ORM for database abstraction & relationships |
| **Flask-JWT-Extended** | 4.6+ | Stateless JSON Web Token authentication |
| **psycopg2-binary** | 2.9+ | PostgreSQL database driver |
| **Gunicorn** | 21.2+ | Production WSGI HTTP server |
| **Pytest** | 8.0+ | Automated unit and integration test runner |

### Frontend
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **Vanilla JavaScript** | ES6+ | Zero-dependency, lightweight, high-performance client logic |
| **Bootstrap** | 5.3.3 | Responsive UI framework & layout grid |
| **Leaflet.js** | 1.9.4 | Interactive maps, polylines, and vehicle markers |
| **Leaflet.draw** | 1.0.4 | Interactive polygon and circle geofence drawing tools |
| **Chart.js** | 4.4+ | Interactive data visualizations & fleet analytics |
| **Bootstrap Icons** | 1.11.3 | Modern vector icons |

### Infrastructure & Cloud
| Service | Role | Configuration |
| :--- | :--- | :--- |
| **Render** | Backend Web Service | Python 3.10 environment running Gunicorn workers |
| **Vercel** | Frontend Edge Hosting | Static site delivery with `/api/*` reverse proxy rewrites |
| **Supabase** | Cloud Database | Managed PostgreSQL with connection pooling & SSL |

---

## 4. User Roles & Access Matrix

The system implements Role-Based Access Control (RBAC) enforced via JWT claims:

| Capability | Admin | Fleet Manager | Dispatcher | Driver | Viewer |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Full Organization Control | ✅ | ❌ | ❌ | ❌ | ❌ |
| Create / Edit Vehicles | ✅ | ✅ | ❌ | ❌ | ❌ |
| Create / Edit Drivers | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage Geofences | ✅ | ✅ | ✅ | ❌ | ❌ |
| Dispatch & Assign Trips | ✅ | ✅ | ✅ | ❌ | ❌ |
| View Live Fleet Radar | ✅ | ✅ | ✅ | ✅ | ✅ |
| Access Mobile Tracker | ✅ | ✅ | ✅ | ✅ | ❌ |
| Acknowledge Alerts | ✅ | ✅ | ✅ | ❌ | ❌ |
| Export Reports | ✅ | ✅ | ✅ | ❌ | ❌ |
