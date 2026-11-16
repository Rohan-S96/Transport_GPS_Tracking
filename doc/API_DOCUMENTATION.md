# 📖 REST API Documentation: Transport GPS Tracking System

- **API Version**: `v1`
- **Default Base URL (Local)**: `http://localhost:5000/api/v1`
- **Production Base URL (Render / Vercel)**: `https://<your-domain>/api/v1`
- **Content-Type**: `application/json`

---

## 🔐 Authentication & Headers

Protected endpoints require a JSON Web Token (JWT) passed in the `Authorization` header:

```http
Authorization: Bearer <jwt_access_token>
```

### Standard Response Envelope
All API endpoints return JSON conforming to the standard structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2026-11-16T08:30:00Z"
}
```

### Standard Paginated Envelope
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_records": 48,
    "total_pages": 3
  },
  "timestamp": "2026-11-16T08:30:00Z"
}
```

### Standard Error Envelope
```json
{
  "success": false,
  "error": "Error message description",
  "code": 400,
  "timestamp": "2026-11-16T08:30:00Z"
}
```

---

## 1. Authentication Endpoints

### 1.1 Register Account
`POST /auth/register`

Creates a new user account and root organization tenant.

```json
// Request Body
{
  "first_name": "Rohan",
  "last_name": "Saste",
  "email": "rohan@example.com",
  "password": "StrongPassword123!",
  "organization_name": "Swift Logistics Corp",
  "role": "fleet_manager"
}
```

```json
// Response 201 Created
{
  "success": true,
  "data": {
    "user_id": "8f9024b1-...",
    "email": "rohan@example.com",
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "role": "fleet_manager",
    "organization": {
      "id": "1e813f44-...",
      "name": "Swift Logistics Corp"
    }
  }
}
```

### 1.2 Login
`POST /auth/login`

```json
// Request Body
{
  "email": "rohan@example.com",
  "password": "StrongPassword123!"
}
```

```json
// Response 200 OK
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "user": {
      "id": "8f9024b1-...",
      "first_name": "Rohan",
      "last_name": "Saste",
      "role": "fleet_manager",
      "organization_id": "1e813f44-..."
    }
  }
}
```

### 1.3 Get Current Profile
`GET /auth/profile` *(Requires Auth)*

Returns profile metadata and active session claims for the authenticated user.

---

## 2. GPS Telemetry & Tracking Endpoints

### 2.1 Ingest Telemetry Packet
`POST /gps/locations` *(Public or Machine API Key)*

Streams a single GPS coordinate packet from either a hardware GPS tracker or driver smartphone.

```json
// Request Body
{
  "registration_number": "MH-04-AB-1234",  // OR "vehicle_id", OR "device_imei"
  "latitude": 19.0760,
  "longitude": 72.8777,
  "speed_kmh": 45.2,
  "heading": 135.0,
  "altitude": 14.5,
  "battery_pct": 82.0,
  "ignition": true,
  "timestamp": "2026-11-16T08:30:00Z"
}
```

```json
// Response 201 Created
{
  "success": true,
  "data": {
    "telemetry_id": "55c4d3...",
    "vehicle_id": "a1b2c3...",
    "registration_number": "MH-04-AB-1234",
    "odometer_km": 14205.8,
    "alerts_generated": 0
  },
  "message": "GPS location recorded"
}
```

### 2.2 Device Connect (Online Signal)
`POST /gps/connect` *(Also accepts GET, Form-Data, or Query Params)*

Explicitly marks a vehicle as **Online** when mobile tracking starts.

```json
// Request Body
{
  "registration_number": "MH-04-AB-1234"
}
```

```json
// Response 200 OK
{
  "success": true,
  "data": {
    "vehicle_id": "a1b2c3...",
    "registration_number": "MH-04-AB-1234",
    "status": "active",
    "is_online": true
  },
  "message": "Vehicle connected and online"
}
```

### 2.3 Device Disconnect (Offline Signal)
`POST /gps/disconnect` *(Also accepts GET, Form-Data, or Query Params)*

Explicitly marks a vehicle as **Offline** when mobile tracking stops or browser is closed (`sendBeacon`).

```json
// Request Body
{
  "registration_number": "MH-04-AB-1234"
}
```

```json
// Response 200 OK
{
  "success": true,
  "data": {
    "vehicle_id": "a1b2c3...",
    "registration_number": "MH-04-AB-1234",
    "status": "offline",
    "is_online": false
  },
  "message": "Vehicle disconnected and offline"
}
```

### 2.4 Live Fleet Snapshot
`GET /gps/live` *(Requires Auth)*

Returns the latest real-time GPS coordinate, online/offline status, driver assignment, speed, and heading for all vehicles in the user's organization.

```json
// Response 200 OK
{
  "success": true,
  "data": [
    {
      "vehicle_id": "a1b2c3...",
      "registration_number": "MH-04-AB-1234",
      "make_model": "Tata Prima 5530.S",
      "status": "active",
      "is_online": true,
      "driver_name": "Rohan Saste",
      "latitude": 19.0760,
      "longitude": 72.8777,
      "speed_kmh": 45.2,
      "heading": 135.0,
      "ignition": true,
      "battery_pct": 82.0,
      "fuel_level_pct": 68.0,
      "odometer_km": 14205.8,
      "last_updated": "2026-11-16T08:30:00+00:00",
      "tracking_source": "mobile_phone",
      "has_hardware_device": false,
      "device_imei": null
    }
  ]
}
```

### 2.5 Historical GPS Breadcrumbs
`GET /trucks/<truck_id>/gps-history?start=...&end=...&limit=500` *(Requires Auth)*

Returns chronological GPS telemetry points for route playback, speed profiling, and stop analysis.

---

## 3. Vehicle & Fleet Management

### 3.1 List Vehicles
`GET /vehicles?page=1&limit=20&status=online&search=MH` *(Requires Auth)*

Supported query parameters:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `search`: Search filter matching plate, make, or model
- `status`: Filter by `online`, `offline`, `active`, `idle`, or `maintenance`
- `include_telemetry`: `true` to include the latest telemetry point

### 3.2 Public Vehicle Roster
`GET /vehicles/public-roster` *(Public)*

Lightweight endpoint returning active fleet registration numbers, make, model, and assigned driver. Used by driver mobile web tracker without login friction.

### 3.3 Register Vehicle
`POST /vehicles` *(Requires fleet_manager or admin)*

```json
{
  "registration_number": "MH-04-AB-1234",
  "make": "Tata Motors",
  "model": "Prima 5530.S",
  "year": 2024,
  "color": "White",
  "fuel_type": "diesel",
  "fuel_capacity_litres": 300,
  "speed_limit_kmh": 80,
  "assigned_driver_id": "...",
  "gps_device_imei": "860123456789012"
}
```

---

## 4. Geofences & Spatial Safety

### 4.1 List Geofences
`GET /geofences` *(Requires Auth)*

Returns all geofences (circular and polygon) configured for the tenant.

### 4.2 Create Geofence
`POST /geofences` *(Requires dispatcher or above)*

```json
// Circular Geofence
{
  "name": "Bhiwandi Central Depot",
  "geofence_type": "circle",
  "latitude": 19.2812,
  "longitude": 73.0489,
  "radius_meters": 500,
  "alert_on_entry": true,
  "alert_on_exit": true
}

// Polygon Geofence
{
  "name": "Nhava Sheva Port Zone",
  "geofence_type": "polygon",
  "coordinates": [
    {"lat": 18.948, "lng": 72.942},
    {"lat": 18.955, "lng": 72.955},
    {"lat": 18.940, "lng": 72.960},
    {"lat": 18.948, "lng": 72.942}
  ],
  "alert_on_entry": true,
  "alert_on_exit": true
}
```

---

## 5. Trips & Cargo Manifests

### 5.1 Create / Dispatch Trip
`POST /trips` *(Requires dispatcher or above)*

```json
{
  "vehicle_id": "...",
  "driver_id": "...",
  "origin_company_id": "...",
  "destination_company_id": "...",
  "origin_address": "Mumbai Port Terminal",
  "destination_address": "Pune Chakan Industrial Hub",
  "cargo_type": "Automotive Components",
  "cargo_weight_kg": 12500,
  "scheduled_departure": "2026-11-17T06:00:00Z"
}
```

### 5.2 Detect Stationary Stops
`GET /trips/<trip_id>/stops` *(Requires Auth)*

Analyzes GPS points between trip start and finish to identify stops exceeding minimum dwell duration (e.g., $\ge 120\text{s}$).

---

## 6. Alerts & Analytics

### 6.1 Incident Alerts
`GET /alerts?status=open&severity=critical` *(Requires Auth)*

### 6.2 Acknowledge / Resolve Alert
`POST /alerts/<alert_id>/acknowledge`  
`POST /alerts/<alert_id>/resolve`

### 6.3 Executive Dashboard Analytics
`GET /analytics/dashboard` *(Requires Auth)*

Returns summary fleet utilization, active vehicles, driver counts, mileage covered today, fuel estimates, and incident breakdown.
