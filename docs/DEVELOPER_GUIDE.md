# 💻 Developer & Operations Guide: Transport GPS Tracking System

This guide outlines setup instructions, coding conventions, testing procedures, and troubleshooting workflows for contributing to the **Transport GPS Tracking System**.

---

## 1. Local Development Setup

### Prerequisites
- **Python**: Version 3.10 or higher
- **Git**
- Modern Web Browser (Chrome, Safari, Firefox, Edge)

### Step 1: Clone Repository
```bash
git clone https://github.com/Rohan-S96/Transport_GPS_Tracking.git
cd Transport_GPS_Tracking
```

### Step 2: Configure Backend Environment
```bash
cd backend
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell / Command Prompt):
.venv\Scripts\activate

# Install dependencies:
pip install -r requirements.txt
```

### Step 3: Configure `.env`
Create `.env` in the `backend/` directory:
```env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-insecure-secret-key-123456
JWT_SECRET_KEY=dev-jwt-secret-key-abcdef
DATABASE_URL=sqlite:///transport_gps_dev.db
ONLINE_HEARTBEAT_TIMEOUT_SECONDS=60
```
*(By default, omitting `DATABASE_URL` uses local SQLite in `backend/instance/transport_gps_dev.db`, so you do not need PostgreSQL running locally).*

### Step 4: Run the Development Server
```bash
python run.py
```
Backend will start on `http://127.0.0.1:5000`. Database tables are automatically initialized upon startup.

### Step 5: Serve Frontend
In a new terminal window:
```bash
cd frontend
python -m http.server 3000
```
Open `http://localhost:3000` in your web browser.

---

## 2. Running Automated Tests

The backend test suite is powered by `pytest` and runs against an isolated in-memory or temporary SQLite database.

```bash
# Run all tests
backend\.venv\Scripts\python -m pytest backend/tests

# Run with verbose output
backend\.venv\Scripts\python -m pytest backend/tests -v

# Run a specific test suite
backend\.venv\Scripts\python -m pytest backend/tests/test_tracking.py
```

### Test Coverage Areas
1. **`test_auth.py`**: User registration, login, token refresh, and profile retrieval.
2. **`test_vehicles.py`**: Vehicle CRUD, duplicate plate protection, and online/offline status queries.
3. **`test_tracking.py`**: Telemetry ingestion, overspeed detection, mobile connect/disconnect, and public roster.
4. **`test_geofence.py`**: Circular and polygon geofence creation and ray-casting collision math.
5. **`test_trips_companies.py`**: Trip dispatch, status progression, and client company associations.
6. **`test_analytics.py`**: Dashboard KPI aggregations and metric summaries.

---

## 3. Architecture & Code Conventions

### 1. Service Layer Pattern
Never write business logic or raw database transactions directly inside route functions.
- Routes (`app/routes/*`): Responsible **only** for request parameter parsing, validation, and invoking service methods.
- Services (`app/services/*`): Pure Python classes containing business logic, math, alert evaluations, and database commits.

### 2. Timezone Standards
- **Always store and serialize datetimes in UTC**.
- When creating datetime objects in Python:
  ```python
  from datetime import datetime, timezone
  now_utc = datetime.now(timezone.utc)
  ```
- Naive datetime strings cause local browser offset bugs (e.g., 5.5-hour delay in Indian Standard Time). When returning timestamps via JSON, ensure they include an explicit UTC indicator (`+00:00` or `Z`).

### 3. Error Handling
Use the standard response utilities:
```python
from app.utils.response_utils import success_response, error_response

# Return success:
return success_response(data, message="Created", code=201)

# Return error:
return error_response("Invalid registration number", code=422)
```

---

## 4. Troubleshooting Common Issues

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `psycopg2.OperationalError: tenant not found` | Using old Supabase direct connection instead of Session Pooler. | Use the Supabase pooler host on port `5432` with `sslmode=require`. |
| Vehicles stuck in `Offline` | Old telemetry timestamp dominating recent connect signal. | Resolved in `TrackingService` by taking `max(candidates)` across `telemetry.recorded_at` and `vehicle.updated_at`. |
| Disconnect beacon returns `422` | Browser `navigator.sendBeacon` sends plain text or blob. | `connect_gps` & `disconnect_gps` parse `request.data`, `request.form`, `request.args`, and `request.json`. |
| Map tiles show "API Key Required" | Using deprecated proprietary third-party tile providers. | Standardized on OpenStreetMap tile servers (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`). |
