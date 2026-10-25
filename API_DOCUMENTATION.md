# 📡 Transport GPS Tracking API Documentation

Base URL (Local): `http://localhost:5000/api/v1`  
Base URL (Railway Production): `https://<your-railway-app>.up.railway.app/api/v1`

All requests expecting JSON must provide the header:  
`Content-Type: application/json`

Authenticated endpoints require a Bearer token in the `Authorization` header:  
`Authorization: Bearer <jwt_access_token>`

---

## Standard Response Envelopes

### Success Response
```json
{
  "success": true,
  "message": "Resource retrieved successfully",
  "data": { ... },
  "timestamp": "2026-10-13T13:30:00Z"
}
```

### Paginated Response
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_records": 150,
    "total_pages": 8
  },
  "timestamp": "2026-10-13T13:30:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Resource not found",
  "code": 404,
  "timestamp": "2026-10-13T13:30:00Z"
}
```

---

## 1. System & Health

### `GET /health`
Returns system status, database connectivity, and server uptime.
- **Auth**: None
- **Response `200 OK`**:
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

## 2. Authentication (`/auth`)

### `POST /auth/register`
Create a new tenant / manager account.
- **Auth**: None
- **Request Body**:
```json
{
  "email": "manager@fleetcorp.com",
  "password": "SecurePassword123!",
  "first_name": "Rohan",
  "last_name": "Sharma",
  "organization_name": "Fleet Corp Logistics",
  "role": "admin"
}
```
- **Response `201 Created`**:
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user_id": "usr_94e50889-1122",
    "email": "manager@fleetcorp.com",
    "role": "admin"
  }
}
```

### `POST /auth/login`
Authenticate user credentials and obtain JWT tokens.
- **Auth**: None
- **Request Body**:
```json
{
  "email": "manager@fleetcorp.com",
  "password": "SecurePassword123!"
}
```
- **Response `200 OK`**:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": "usr_94e50889-1122",
      "email": "manager@fleetcorp.com",
      "full_name": "Rohan Sharma",
      "role": "admin",
      "organization_id": "org_1122"
    }
  }
}
```

### `GET /auth/me`
Retrieve currently logged-in user profile.
- **Auth**: Bearer Token
- **Response `200 OK`**:
```json
{
  "success": true,
  "data": {
    "id": "usr_94e50889-1122",
    "email": "manager@fleetcorp.com",
    "first_name": "Rohan",
    "last_name": "Sharma",
    "role": "admin",
    "created_at": "2026-10-10T08:00:00Z"
  }
}
```

---

## 3. Vehicles (`/vehicles`)

### `GET /vehicles`
Retrieve fleet vehicles with status and latest telemetry summary.
- **Auth**: Bearer Token
- **Query Params**: `status` (active|idle|maintenance|offline), `search`, `page`, `limit`
- **Response `200 OK`**:
```json
{
  "success": true,
  "data": [
    {
      "id": "veh_01",
      "registration_number": "MH-12-AB-1234",
      "make": "Tata",
      "model": "Prima 4028.S",
      "vin": "MAT428123XYZ999",
      "device_imei": "864201048821931",
      "status": "active",
      "assigned_driver": {
        "id": "drv_01",
        "name": "Rajesh Kumar"
      },
      "last_known_telemetry": {
        "latitude": 19.0760,
        "longitude": 72.8777,
        "speed": 62.4,
        "heading": 145,
        "battery_pct": 94,
        "recorded_at": "2026-10-13T13:28:40Z"
      }
    }
  ],
  "pagination": { "page": 1, "limit": 20, "total_records": 12 }
}
```

### `POST /vehicles`
Register a new vehicle.
- **Auth**: Bearer Token (Admin / Dispatcher)
- **Request Body**:
```json
{
  "registration_number": "MH-04-DE-5678",
  "make": "BharatBenz",
  "model": "2823R",
  "year": 2024,
  "vin": "BBNZ2823R2024001",
  "device_imei": "864201048899881",
  "fuel_type": "diesel",
  "fuel_capacity_litres": 380,
  "driver_id": "drv_02"
}
```
- **Response `201 Created`**:
```json
{
  "success": true,
  "message": "Vehicle registered successfully",
  "data": { "id": "veh_02", "registration_number": "MH-04-DE-5678" }
}
```

### `GET /vehicles/{id}`
Retrieve vehicle details including specifications, odometer, and telemetry logs.

### `PUT /vehicles/{id}`
Update vehicle details, status, or driver assignment.

### `DELETE /vehicles/{id}`
Soft delete or remove vehicle from fleet roster.

---

## 4. Live Tracking & Telemetry (`/tracking`)

### `POST /tracking/telemetry`
Ingest raw GPS telemetry packet from IoT devices or mobile trackers.
- **Auth**: Bearer Token or Device API Key
- **Request Body**:
```json
{
  "device_imei": "864201048821931",
  "latitude": 19.0820,
  "longitude": 72.8850,
  "altitude": 14.2,
  "speed": 64.5,
  "heading": 138,
  "satellites": 12,
  "ignition": true,
  "battery_pct": 92,
  "odometer_km": 48201.8,
  "fuel_level_pct": 78.4,
  "timestamp": "2026-10-13T13:30:10Z"
}
```
- **Response `201 Created`**:
```json
{
  "success": true,
  "message": "Telemetry received and evaluated",
  "alerts_generated": 0
}
```

### `GET /tracking/live`
Retrieve latest positions of all active vehicles for the Leaflet live map.
- **Auth**: Bearer Token
- **Response `200 OK`**:
```json
{
  "success": true,
  "data": [
    {
      "vehicle_id": "veh_01",
      "registration_number": "MH-12-AB-1234",
      "status": "active",
      "speed": 64.5,
      "heading": 138,
      "latitude": 19.0820,
      "longitude": 72.8850,
      "ignition": true,
      "driver_name": "Rajesh Kumar",
      "last_updated": "2026-10-13T13:30:10Z"
    }
  ]
}
```

### `GET /tracking/history/{vehicle_id}`
Retrieve historical breadcrumb coordinate trail for route playback.
- **Auth**: Bearer Token
- **Query Params**: `start_time` (ISO), `end_time` (ISO), `step_limit` (default 500)
- **Response `200 OK`**:
```json
{
  "success": true,
  "vehicle_id": "veh_01",
  "points_count": 280,
  "data": [
    {
      "latitude": 19.0760,
      "longitude": 72.8777,
      "speed": 55.0,
      "heading": 140,
      "timestamp": "2026-10-13T09:00:00Z"
    }
  ]
}
```

---

## 5. Geofences (`/geofences`)

### `GET /geofences`
List all defined geofences (circular and polygon zones).
- **Auth**: Bearer Token

### `POST /geofences`
Create a new geofence boundary.
- **Auth**: Bearer Token
- **Request Body (Circle)**:
```json
{
  "name": "Bhiwandi Central Hub",
  "fence_type": "circle",
  "center_latitude": 19.2965,
  "center_longitude": 73.0631,
  "radius_meters": 1500,
  "alert_on_entry": true,
  "alert_on_exit": true,
  "color": "#3B82F6"
}
```
- **Request Body (Polygon)**:
```json
{
  "name": "JNPT Port Depot",
  "fence_type": "polygon",
  "coordinates": [
    [18.9482, 72.9463],
    [18.9550, 72.9600],
    [18.9400, 72.9650],
    [18.9482, 72.9463]
  ],
  "alert_on_entry": true,
  "alert_on_exit": true,
  "color": "#10B981"
}
```

---

## 6. Alerts (`/alerts`)

### `GET /alerts`
Retrieve trigger alerts (overspeeding, geofence breaches, SOS, battery).
- **Auth**: Bearer Token
- **Query Params**: `severity` (info|warning|critical), `status` (unresolved|resolved), `page`, `limit`
- **Response `200 OK`**:
```json
{
  "success": true,
  "data": [
    {
      "id": "alt_101",
      "vehicle_id": "veh_01",
      "registration_number": "MH-12-AB-1234",
      "alert_type": "overspeed",
      "severity": "warning",
      "message": "Vehicle exceeded 80 km/h limit (recorded 94 km/h)",
      "latitude": 19.0910,
      "longitude": 72.8940,
      "is_acknowledged": false,
      "triggered_at": "2026-10-13T13:12:00Z"
    }
  ]
}
```

### `POST /alerts/{id}/acknowledge`
Acknowledge or dismiss an alert with optional resolution note.

---

## 7. Drivers (`/drivers`)

### `GET /drivers`
Get driver directory with license status, assigned vehicles, and safety scores.

### `POST /drivers`
Register a new commercial driver.

---

## 8. Trips (`/trips`)

### `GET /trips`
Retrieve calculated vehicle trips, duration, idle time, and fuel estimates.

### `GET /trips/{id}/playback`
Retrieve sequenced waypoint coordinates for animated map playback.

---

## 9. Analytics & Reports (`/analytics`)

### `GET /analytics/summary`
Fleet KPIs: total vehicles, active on road, idle, total distance covered today, fuel index.

### `GET /analytics/export?type=vehicles&format=excel`
Exports fleet data or trip records as `.xlsx` (via openpyxl/pandas) or `.csv`.
