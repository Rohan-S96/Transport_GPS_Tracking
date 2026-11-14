# Transport GPS Tracking & Fleet Management &mdash; Complete Codebase Architecture & Code Explanation Guide

This guide provides a comprehensive, end-to-end breakdown of the entire **Transport GPS Tracking** project. Every folder, file, and code block is explained in clear English, detailing its role, architecture, inputs, outputs, and how it interacts with other parts of the system.

---

## Table of Contents
1. [High-Level Architectural Overview](#1-high-level-architectural-overview)
2. [Project Root & Deployment Configuration](#2-project-root--deployment-configuration)
3. [Backend Core Architecture (`backend/`)](#3-backend-core-architecture-backend)
   - [Application Entrypoints & Config](#application-entrypoints--config)
   - [Database Models (`backend/app/models/`)](#database-models-backendappmodels)
   - [API Route Controllers (`backend/app/routes/`)](#api-route-controllers-backendapproutes)
   - [Business Logic Services (`backend/app/services/`)](#business-logic-services-backendappservices)
   - [Utilities & Geo-Math (`backend/app/utils/`)](#utilities--geo-math-backendapputils)
   - [Automated Test Suite (`backend/tests/`)](#automated-test-suite-backendtests)
4. [Frontend Architecture (`frontend/`)](#4-frontend-architecture-frontend)
   - [Core Client Libraries (`frontend/assets/js/`)](#core-client-libraries-frontendassetsjs)
   - [Leaflet Map Engine (`map.js`)](#leaflet-map-engine-mapjs)
   - [Mobile Driver Tracker (`driver-tracker.html` & `driver-tracker.js`)](#mobile-driver-tracker)
   - [Fleet Operations Pages & Controllers](#fleet-operations-pages--controllers)
   - [Design System & Stylesheets (`frontend/assets/css/`)](#design-system--stylesheets-frontendassetscss)
5. [Telemetry & Tracking Lifecycles Explained](#5-telemetry--tracking-lifecycles-explained)

---

## 1. High-Level Architectural Overview

The application is structured as a **decoupled Client-Server Architecture**:
* **Backend:** Built with Python (Flask 2.3+), SQLAlchemy ORM, Flask-JWT-Extended for token authentication, and Alembic for schema migrations. It exposes a RESTful JSON API under `/api/v1/`.
* **Frontend:** Built with vanilla HTML5, Bootstrap 5.3 (dark theme), Leaflet.js 1.9 for interactive mapping, Chart.js for telemetry analytics, and QR Code generation for driver onboarding.
* **Database Support:** Supports SQLite (local development) and PostgreSQL with PostGIS-ready schemas (production on Render / Railway / Supabase).

### System Data Flow Diagram

```
[ Driver Smartphone GPS ]     [ Hardware GPS Kits (Teltonika/Sinotrack) ]
           │                                      │
           │ (HTTP JSON Coordinates)              │ (IMEI + GPS Packet)
           ▼                                      ▼
      POST /api/v1/gps/locations  (or /api/v1/tracking/telemetry)
                                  │
                                  ▼
                     [ TrackingService.process_telemetry ]
                      ├── 1. Resolve Vehicle (UUID / IMEI / Reg No)
                      ├── 2. Haversine Formula -> Cumulative Odometer
                      ├── 3. Persist GPSTelemetry Point
                      ├── 4. Evaluate AlertService (Overspeed check)
                      ├── 5. Evaluate GeofenceService (In/Out checks)
                      └── 6. Commit to Database
                                  │
                                  ▼
           [ Dispatcher Operations Radar (live-tracking.html) ]
             ├── Polls GET /api/v1/gps/live every 4 seconds
             ├── Updates Leaflet Markers with Heading & Status
             └── Shows Telemetry (Speed, Battery, Distance, Source)
```

---

## 2. Project Root & Deployment Configuration

### 1. `README.md`, `API_DOCUMENTATION.md`, `DATABASE_SCHEMA.md`, `DEPLOYMENT.md`
* **`README.md`**: Project landing documentation covering installation, quick start, architecture, environment variables, and REST endpoints.
* **`API_DOCUMENTATION.md`**: Comprehensive contract specification for all REST API endpoints: schemas, query parameters, payloads, status codes, and error formats.
* **`DATABASE_SCHEMA.md`**: Full database entity-relationship documentation: tables, columns, constraints, foreign keys, and indexes.
* **`DEPLOYMENT.md`**: Detailed step-by-step deployment guide for Render, Railway, Vercel, and Docker.

### 2. Deployment Manifests
* **`Procfile`**: Specifies the process command for PaaS platforms (e.g. Render / Heroku):
  ```
  web: gunicorn --chdir backend wsgi:app -w 4 -k gthread --threads 2 --timeout 120
  ```
  *Explanation:* Launches the Gunicorn WSGI server with 4 worker processes and 2 threads per worker, allowing simultaneous handling of multiple incoming GPS telemetry streams.
* **`railway.json`**: Railway builder configuration pointing to `backend/Dockerfile` or Nixpacks.
* **`vercel.json`**: Vercel configuration for static frontend hosting and API proxy routing.
* **`.env.example`**: Template environment variable file documenting database credentials, JWT secret keys, CORS origins, and alert thresholds.

---

## 3. Backend Core Architecture (`backend/`)

### Application Entrypoints & Config

#### `backend/run.py`
The local development server entrypoint.
* **Code:**
  ```python
  app = create_app(os.getenv("APP_ENV", "development"))
  if __name__ == "__main__":
      port = int(os.getenv("PORT", 5000))
      app.run(host="0.0.0.0", port=port, debug=True)
  ```
* **Explanation:** Reads the environment variable to instantiate the application via the Application Factory (`create_app`), binding to all network interfaces (`0.0.0.0`) on port 5000 with auto-reload enabled.

#### `backend/wsgi.py`
The production WSGI entrypoint consumed by Gunicorn or uWSGI in production.

#### `backend/app/config.py`
Defines environment-based configuration classes: `DevelopmentConfig`, `TestingConfig`, and `ProductionConfig`.
* **Key Configuration Values:**
  * `SQLALCHEMY_DATABASE_URI`: Database connection string (cleanses whitespace and URL encoding for PostgreSQL / SQLite).
  * `JWT_SECRET_KEY` & `JWT_ACCESS_TOKEN_EXPIRES`: Configures JSON Web Token generation (defaults to 12 hours).
  * `OVERSPEED_THRESHOLD_KMH`: Fleet-wide maximum allowed speed (default 80.0 km/h).
  * `OFFLINE_TRUCK_MINUTES`: Interval (default 10 minutes) after which an inactive truck is marked offline.
  * `STOP_MIN_DURATION_MINUTES`: Minimum stationary period (default 5 minutes) before the system detects an operational truck stop.

#### `backend/app/extensions.py`
Instantiates unattached Flask extension instances to avoid circular imports:
* `db = SQLAlchemy()`: Object-Relational Mapper.
* `migrate = Migrate()`: Database schema migration engine.
* `jwt = JWTManager()`: Authentication and JWT claims manager.
* `cors = CORS()`: Cross-Origin Resource Sharing handler.

#### `backend/app/__init__.py` (Application Factory)
* **Function: `create_app(config_name)`**
  1. Initializes the Flask instance.
  2. Loads configuration settings from `config.py`.
  3. Binds extensions (`db`, `migrate`, `jwt`, `cors`).
  4. Registers all 12 Blueprint route modules:
     * `/api/v1/auth`, `/api/v1/vehicles`, `/api/v1/gps`, `/api/v1/trips`, `/api/v1/drivers`, `/api/v1/geofences`, `/api/v1/alerts`, `/api/v1/companies`, `/api/v1/maintenance`, `/api/v1/users`, `/api/v1/analytics`, `/api/v1/health`.
  5. Sets up JWT token error handlers and automatic database seeding.

---

### Database Models (`backend/app/models/`)

Every model inherits from `db.Model` and includes a `.to_dict()` serialization method.

#### 1. `vehicle.py` (`Vehicle` model)
* **Purpose:** Represents a truck or fleet asset.
* **Columns:**
  * `id`: UUID (Primary Key).
  * `organization_id`: Multi-tenant company identifier.
  * `assigned_driver_id`: Foreign key pointing to `drivers.id`.
  * `registration_number`: Unique license plate (e.g., `MH-12-RN-4501`).
  * `vin`, `make`, `model`, `year`, `color`, `fuel_type`, `fuel_capacity_litres`.
  * `status`: Vehicle status (`active`, `idle`, `maintenance`, `offline`, `decommissioned`).
  * `current_odometer_km`: Cumulative mileage accumulated from GPS points.
  * `speed_limit_kmh`: Vehicle-specific overspeed threshold override.
* **Relationships:** One-to-One with `GPSDevice`, One-to-Many with `GPSTelemetry`, `Trip`, `Alert`, `MaintenanceLog`, `FuelLog`.

#### 2. `gps_device.py` (`GPSDevice` model)
* **Purpose:** Represents physical GPS tracking hardware mounted inside a vehicle.
* **Columns:**
  * `id`: UUID.
  * `vehicle_id`: Foreign Key pointing to `vehicles.id` (Unique, 1-to-1).
  * `imei`: Unique 15-digit International Mobile Equipment Identity number.
  * `manufacturer`, `model` (e.g. Teltonika FMB920, Sinotrack ST-901).
  * `sim_iccid`, `sim_phone`: Cellular SIM card identifiers.
  * `status`: Device health (`active`, `inactive`, `decommissioned`).
  * `last_seen_at`: Timestamp of the most recent telemetry packet received.

#### 3. `gps_telemetry.py` (`GPSTelemetry` model)
* **Purpose:** High-frequency time-series coordinate log.
* **Columns:**
  * `id`: BigInteger auto-incrementing ID.
  * `vehicle_id`: Foreign key to `vehicles.id` (Indexed).
  * `latitude`, `longitude`: 6-decimal floating point coordinates.
  * `speed_kmh`, `heading`, `altitude`, `satellites`.
  * `ignition`: Boolean engine status.
  * `battery_pct`: Battery percentage (device battery or driver phone battery).
  * `odometer_km`: Current vehicle odometer reading at this timestamp.
  * `recorded_at`: Time reported by GPS hardware / smartphone.
  * `created_at`: Server timestamp when packet was ingested.
* **Indexes:** Composite index `(vehicle_id, recorded_at)` for millisecond query performance during historical route playback.

#### 4. `driver.py` (`Driver` model)
* **Purpose:** Commercial vehicle driver roster.
* **Columns:** `id`, `first_name`, `last_name`, `license_number`, `phone_number`, `safety_score` (0-100), `status` (`available`, `on_trip`, `off_duty`, `suspended`).

#### 5. `trip.py` (`Trip` & `Stop` models)
* **Purpose:** Cargo manifests and point-to-point journey tracking.
* **Columns in `Trip`:** `trip_number`, `vehicle_id`, `driver_id`, `source_company_id`, `destination_company_id`, `planned_distance_km`, `actual_distance_km`, `cargo_description`, `cargo_weight_kg`, `status` (`planned`, `in_progress`, `completed`, `cancelled`).
* **Columns in `Stop`:** Automatic stop detection records capturing where, when, and for how long a truck was stationary during a trip.

#### 6. `geofence.py` (`Geofence` model)
* **Purpose:** Virtual geographic perimeters (circle, polygon, corridor).
* **Columns:** `name`, `fence_type`, `coordinates` (JSON array of vertices or center/radius), `speed_limit_kmh`, `action_on_enter`, `action_on_exit`.

#### 7. `alert.py` (`Alert` model)
* **Purpose:** Fleet safety violations and incident logs.
* **Columns:** `vehicle_id`, `alert_type` (`overspeed`, `geofence_enter`, `geofence_exit`, `truck_offline`, `sos`, `maintenance_due`), `severity` (`low`, `medium`, `high`, `critical`), `latitude`, `longitude`, `speed_kmh`, `message`, `is_acknowledged`.

#### 8. `user.py` (`User` & `Organization` models)
* **Purpose:** Multi-tenant organizations and Role-Based Access Control (RBAC).
* **Roles:** `admin`, `fleet_manager`, `dispatcher`, `viewer`.
* **Security:** Password hashing using Werkzeug scrypt/pbkdf2, JWT claim integration.

#### 9. `company.py`, `maintenance.py`, `audit_log.py`
* **`Company`**: Depots, clients, warehouses, and freight terminals.
* **`MaintenanceLog` & `FuelLog`**: Scheduled servicing, oil changes, tire replacement, fuel fill-ups, and cost auditing.
* **`AuditLog`**: Immutable compliance ledger recording user actions across the platform.

---

### API Route Controllers (`backend/app/routes/`)

#### `tracking_routes.py` (`/api/v1/gps`)
* **`POST /api/v1/gps/locations` (and `/api/v1/tracking/telemetry`)**:
  * **Role:** Primary telemetry ingestion gateway.
  * **Payload accepted:** `{ latitude, longitude, speed_kmh, heading, altitude, battery_pct, ignition }` combined with either `vehicle_id`, `device_imei`, or `registration_number`.
  * **Workflow:** Authenticates payload structure, passes data to `TrackingService.process_telemetry`, returns HTTP 201 with odometer and alert metrics.
* **`GET /api/v1/gps/live`**:
  * **Role:** Returns the latest coordinate snapshot for all trucks in the caller's organization. Used by the live fleet map.
* **`GET /api/v1/gps/live/<truck_id>`**:
  * **Role:** Returns live snapshot for one specific truck.
* **`GET /api/v1/trucks/<truck_id>/gps-history`**:
  * **Role:** Queries historical breadcrumbs between `start_time` and `end_time` for route playback.

#### `vehicle_routes.py` (`/api/v1/vehicles`)
* **`GET /api/v1/vehicles`**: Paginated listing of vehicles with search and status filters.
* **`GET /api/v1/vehicles/public-roster`**:
  * **Role:** Public lightweight endpoint (no JWT required) allowing the **Driver Mobile Tracker** to list trucks and allow drivers to select their vehicle without needing an admin login.
* **`POST /api/v1/vehicles`**: Registers a new truck (requires `fleet_manager` or `admin` role).
* **`PUT /api/v1/vehicles/<id>` & `DELETE /api/v1/vehicles/<id>`**: Updates truck details or marks as decommissioned.
* **`POST /api/v1/vehicles/<id>/gps-device`**: Binds a physical GPS hardware IMEI to a vehicle.

#### Other Route Files:
* **`auth_routes.py`**: User login (`/login`), token refresh (`/refresh`), current user profile (`/me`), and logout.
* **`trip_routes.py`**: Start trip (`/start`), complete trip (`/complete`), cancel, and stop detection (`/detect-stops`).
* **`driver_routes.py`**: Driver management, license auditing, and safety score calculations.
* **`geofence_routes.py`**: CRUD for circular and polygonal geofence perimeters.
* **`alert_routes.py`**: Active alerts feed, alert acknowledgment, and severity filtering.
* **`analytics_routes.py`**: Aggregated fleet metrics: total distance, active vehicle counts, fuel efficiency, and violation statistics.

---

### Business Logic Services (`backend/app/services/`)

#### `tracking_service.py` (`TrackingService`)
The heart of real-time telemetry processing.
* **`process_telemetry(data)` Method Walkthrough:**
  1. **`_resolve_vehicle(data)`**: Resolves the target truck by checking `vehicle_id`, physical hardware `device_imei`, or license `registration_number`.
  2. **Cumulative Odometer**: Computes `haversine_distance_km` between the incoming coordinate and the truck's previous point. Filters out GPS jitter ($< 5\text{ m}$) and impossible jumps ($> 50\text{ km}$ per packet), adding valid delta to `vehicle.current_odometer_km`.
  3. **Persist Telemetry**: Instantiates and commits a `GPSTelemetry` record.
  4. **Status Updating**: If `speed > 3 km/h`, status becomes `active`; if engine ignition is true, status is `idle`; otherwise `offline`.
  5. **Safety Evaluations**: Executes `AlertService.check_overspeed()` and `GeofenceService.check_vehicle_geofences()`.
* **`get_live_fleet_positions()`**:
  Compiles the latest coordinates, speed, battery, and dynamic source identification:
  `"tracking_source": "hardware_gps" if is_hardware else "mobile_phone"`.

#### `alert_service.py` (`AlertService`)
* **`check_overspeed(vehicle, lat, lng, speed)`**: Checks speed against vehicle-specific or organization-wide speed limits. Generates an `Alert` record and marks `severity = "critical"` if overspeeding exceeds limit by $> 20\text{ km/h}$.
* **`generate_geofence_alert(...)`**: Logs perimeter breaches when a truck enters or leaves an authorized yard or depot.

#### `geofence_service.py` (`GeofenceService`)
* Implements mathematical point-in-polygon (Ray-Casting Algorithm) and circle radial distance calculations to determine whether a coordinate is inside or outside defined geofences.

#### `trip_service.py` (`TripService`)
* Manages trip lifecycles, compares planned route distances against actual GPS odometer mileage, and evaluates on-time delivery performance.

---

### Utilities & Geo-Math (`backend/app/utils/`)

#### `geo_utils.py`
* **`haversine_distance_km(lat1, lon1, lat2, lon2)`**:
  Computes the great-circle distance between two GPS coordinates using spherical trigonometry:
  $$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \text{lat}}{2}\right) + \cos(\text{lat}_1)\cos(\text{lat}_2)\sin^2\left(\frac{\Delta \text{lon}}{2}\right)}\right)$$
  where $R = 6371\text{ km}$.
* **`is_point_in_polygon(lat, lng, polygon_coords)`**:
  Ray-Casting algorithm to evaluate whether a truck is inside complex polygonal geofences.

#### `decorators.py`
* **`@min_role(role)`**: Enforces role hierarchy (`viewer` < `dispatcher` < `fleet_manager` < `admin`).
* **`@handle_service_errors`**: Catches ValueError, NotFoundError, and integrity exceptions, formatting them into standardized JSON error responses.

#### `response_utils.py`
* Standardizes all API output formats:
  `{ "success": true, "data": ..., "message": "..." }` or `{ "success": false, "error": "...", "status_code": 4xx }`.

#### `seed_data.py`
* Pre-populates a fresh database with demo organizations, admin credentials (`admin@swifttransport.com`), commercial trucks (`MH-12-RN-4501`), drivers, geofences, and initial coordinates.

---

### Automated Test Suite (`backend/tests/`)

* **`conftest.py`**: Pytest setup creating an isolated in-memory SQLite database (`sqlite:///:memory:`) and test JWT auth client.
* **`test_tracking.py`**: Tests Haversine math, overspeed alert triggering, mobile phone telemetry ingestion via registration number, and public roster discovery.
* **`test_vehicles.py`**, **`test_auth.py`**, **`test_geofence.py`**, **`test_trips_companies.py`**, **`test_analytics.py`**: Complete regression suite ensuring all endpoints meet expected business rules.

---

## 4. Frontend Architecture (`frontend/`)

### Core Client Libraries (`frontend/assets/js/`)

#### 1. `config.js` (`CONFIG` & `PUBLIC_CONFIG`)
* Dynamically switches API base URLs:
  * On localhost: `http://localhost:5000/api/v1`
  * In production: `https://transport-gps-tracking.onrender.com/api/v1`
* Supports runtime overrides saved in `localStorage`.

#### 2. `api.js` (`ApiClient`)
* Centralized HTTP wrapper handling `fetch()`, attaching `Authorization: Bearer <token>` headers, handling HTTP 401 token expirations, and JSON parsing.

#### 3. `auth.js` (`Auth`)
* Manages user session state, saves tokens in `localStorage`, handles login/logout redirection, and decodes JWT roles to show/hide manager features.

#### 4. `utils.js` (`Utils`)
* Utility helpers: toast notifications, date formatting, speed formatting (`X km/h`), and HTML badge rendering (`status-active`, `status-idle`, etc.).

---

### Leaflet Map Engine (`map.js`)

Defines the `FleetMap` class:
* **`init()`**: Initializes Leaflet with OpenStreetMap tiles, custom zoom controls, and default center coordinates.
* **`createVehicleIcon(status, heading)`**: Generates a dynamic HTML `L.divIcon` displaying a truck icon rotated to the vehicle's exact compass heading with an active radar pulse animation.
* **`updateVehicleMarker(vehicle)`**: Updates existing vehicle markers smoothly without re-rendering the whole map. Displays popups showing driver name, current speed, battery level, last seen time, and tracking source (📱 Phone vs 🛰️ Hardware GPS).
* **`renderGeofences(geofences)`**: Draws circular and polygonal geofence layers with customizable boundary colors.

---

### Mobile Driver Tracker (`driver-tracker.html` & `driver-tracker.js`)

A mobile-first Web Application designed for smartphone browsers inside the truck cabin:
* **HTML Structure (`driver-tracker.html`):**
  * Responsive mobile UI with high-contrast night mode.
  * Truck selector dropdown and driver identity inputs.
  * Prominent **START GPS TRACKING** / **STOP TRACKING** action button.
  * Live Cockpit:
    * Digital Speedometer ($0\text{ to }120\text{ km/h}$) with color thresholds.
    * 4 Metrics: GPS Accuracy ($\pm\text{meters}$), Distance Traveled ($\text{km}$), Heading & Compass, Packets Transmitted.
    * Real-time GPS coordinate display.
    * Embedded Mini Leaflet Map with breadcrumb route trail.
* **Controller Logic (`driver-tracker.js`):**
  * **`navigator.geolocation.watchPosition`**: Requests high-accuracy coordinates (`enableHighAccuracy: true, maximumAge: 0`).
  * **Screen WakeLock API**: Acquires `navigator.wakeLock.request('screen')` so the driver's phone display does not turn off and stop tracking while driving.
  * **Battery Status API**: Queries `navigator.getBattery()` to transmit battery percentages.
  * **Offline Resilience Queue**: If cellular signal drops on highways or in tunnels, coordinates are buffered in `localStorage`. Once the network reconnects, buffered packets are automatically flushed to `/api/v1/gps/locations`.
  * **Rate Limiting**: Sends telemetry packets every $3.5\text{ seconds}$ to conserve mobile data while ensuring continuous real-time dispatch tracking.

---

### Fleet Operations Pages & Controllers

#### 1. `index.html` & `dashboard.js` (Executive Overview)
* Displays operational KPIs: Active Moving Fleet, Idle Vehicles, Today's Mileage, Active Incident Alerts.
* Live vehicle telemetry table with real-time status badges.
* Fleet distribution charts using Chart.js.

#### 2. `live-tracking.html` & `live-tracking.js` (Real-Time Radar)
* Split-screen operational cockpit:
  * Left: Searchable list of connected trucks with speed, driver, and tracking source badge (📱 Phone vs 🛰️ GPS Kit).
  * Right: Full-viewport interactive Leaflet map with live vehicle markers and geofences.
  * **"Track via Mobile Phone" Feature**: Modal that lets dispatchers select any truck, generate an instant link (`/driver-tracker.html?v=TRUCK-NO`), render a QR code on canvas, and send the link to the driver via WhatsApp in one click.

#### 3. `playback.html` & `playback.js` (Historical Route Playback)
* Allows dispatchers to select a truck, date, and time range to replay historical trips with play, pause, and speed multiplier ($1\times, 2\times, 5\times, 10\times$) controls.

#### 4. `vehicles.html`, `drivers.html`, `trips.html`, `geofences.html`, `alerts.html`
* Full CRUD interfaces for managing trucks, assigning hardware GPS IMEIs, maintaining driver safety scores, planning cargo trips, defining geofences, and acknowledging safety alerts.

---

### Design System & Stylesheets (`frontend/assets/css/`)

* **`style.css`**: Master design tokens: color variables, dark theme surfaces (`#0B0F19`, `#111827`), navigation sidebars, topbar header styling, and typography.
* **`components.css`**: Reusable component styles: KPI metric cards, gradient borders, status badge pills, data tables, and modal dialogs.
* **`map.css`**: Styles for Leaflet map containers, custom marker pins, pulse animations, vehicle heading rotation, and custom popup cards.

---

## 5. Telemetry & Tracking Lifecycles Explained

### The Mobile Phone Tracking Lifecycle
1. **Dispatcher Setup:** Dispatcher opens `live-tracking.html`, clicks *Track via Mobile Phone*, selects Truck `MH-12-RN-4501`, and shares the WhatsApp link.
2. **Driver Starts Trip:** Driver clicks the link on their smartphone, opening `driver-tracker.html?v=MH-12-RN-4501`.
3. **Permission & Lock:** Driver taps *Start GPS Tracking*. The browser grants high-accuracy GPS permission and activates Screen WakeLock.
4. **Telemetry Ingestion:** Every $3.5\text{ seconds}$, the phone sends a packet to `POST /api/v1/gps/locations`.
5. **Real-Time Visualization:** The truck marker moves on the dispatcher's live map, odometer increases, and the badge indicates 📱 *Driver Mobile GPS*.

### The Hardware GPS Kit Upgrade Lifecycle
1. **Device Installation:** Physical GPS tracker (e.g., Teltonika FMB920) is installed and connected to vehicle power.
2. **Device Configuration:** The device is configured with APN to send HTTP POST telemetry to `https://<domain>/api/v1/gps/locations` with its 15-digit IMEI.
3. **IMEI Assignment:** The dispatcher inputs the IMEI under *Vehicles & Trucks -> Manage GPS Device*.
4. **Seamless Switch:** When packets arrive with `device_imei`, the system links them to that vehicle, switching the map badge from 📱 *Phone* to 🛰️ *Hardware GPS Kit* without any code changes or downtime.
