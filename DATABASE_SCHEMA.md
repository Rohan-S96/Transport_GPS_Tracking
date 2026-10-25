# 🗄️ Transport GPS Tracking Database Schema

The system utilizes **PostgreSQL** hosted on **Supabase**. The schema is optimized for both relational enterprise entities (Users, Vehicles, Drivers) and high-throughput time-series records (GPS Telemetry, Alerts, Trips).

---

## Entity Relationship Overview

```text
Organizations (1) ───< Users (N)
Organizations (1) ───< Vehicles (N)
Organizations (1) ───< Drivers (N)
Organizations (1) ───< Geofences (N)

Vehicles (1) ───< GPS_Telemetry (N)
Vehicles (1) ───< Alerts (N)
Vehicles (1) ───< Trips (N)
Vehicles (1) ───< Maintenance_Logs (N)
Vehicles (1) ───< Fuel_Logs (N)

Drivers (1) ───< Vehicles (0..1)
Drivers (1) ───< Trips (N)
```

---

## 1. `organizations`
Represents the tenant or fleet company owning the assets.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID / VARCHAR(36) | PRIMARY KEY | Unique organization ID |
| `name` | VARCHAR(120) | NOT NULL | Company name (e.g. Swift Logistics) |
| `contact_email` | VARCHAR(120) | NOT NULL | Primary contact email |
| `contact_phone` | VARCHAR(25) | NULL | Primary contact phone |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Last update timestamp |

---

## 2. `users`
System operators, fleet managers, and dispatchers.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique user ID |
| `organization_id`| VARCHAR(36) | FOREIGN KEY (organizations.id) | Tenant reference |
| `email` | VARCHAR(120) | UNIQUE, NOT NULL | Account login email |
| `password_hash` | VARCHAR(255) | NOT NULL | Salted cryptographic password hash |
| `first_name` | VARCHAR(60) | NOT NULL | First name |
| `last_name` | VARCHAR(60) | NOT NULL | Last name |
| `role` | VARCHAR(20) | NOT NULL, DEFAULT 'manager' | `admin`, `manager`, `dispatcher`, `driver` |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active flag |
| `last_login_at` | TIMESTAMPTZ | NULL | Last login timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Record creation |

---

## 3. `drivers`
Professional drivers assigned to vehicles.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Driver identifier |
| `organization_id`| VARCHAR(36) | FOREIGN KEY (organizations.id) | Tenant reference |
| `first_name` | VARCHAR(60) | NOT NULL | Driver first name |
| `last_name` | VARCHAR(60) | NOT NULL | Driver last name |
| `license_number`| VARCHAR(50) | UNIQUE, NOT NULL | Commercial driving license ID |
| `phone_number` | VARCHAR(25) | NOT NULL | Contact mobile number |
| `safety_score` | FLOAT | NOT NULL, DEFAULT 100.0 | Calculated driver safety rating (0-100) |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'available' | `available`, `on_trip`, `off_duty` |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |

---

## 4. `vehicles`
Fleet vehicles (trucks, vans, buses, trailers).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Unique vehicle ID |
| `organization_id`| VARCHAR(36) | FOREIGN KEY (organizations.id) | Tenant reference |
| `assigned_driver_id`| VARCHAR(36)| FOREIGN KEY (drivers.id) NULL | Currently assigned driver |
| `registration_number`| VARCHAR(30)| UNIQUE, NOT NULL | License plate / Registration |
| `vin` | VARCHAR(50) | UNIQUE, NULL | Vehicle Identification Number |
| `make` | VARCHAR(60) | NOT NULL | Manufacturer (e.g. Tata, Volvo) |
| `model` | VARCHAR(60) | NOT NULL | Model designation |
| `year` | INTEGER | NULL | Model year |
| `device_imei` | VARCHAR(30) | UNIQUE, NULL | GPS tracker hardware IMEI |
| `fuel_type` | VARCHAR(20) | DEFAULT 'diesel' | `diesel`, `petrol`, `electric`, `cng` |
| `fuel_capacity_litres`| FLOAT | DEFAULT 300.0 | Maximum fuel tank volume |
| `status` | VARCHAR(20) | DEFAULT 'active' | `active`, `idle`, `maintenance`, `offline` |
| `current_odometer_km` | FLOAT | DEFAULT 0.0 | Current odometer tally |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |

---

## 5. `gps_telemetry`
High-volume historical and real-time GPS coordinate packets.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGSERIAL / BIGINT | PRIMARY KEY | Auto-incrementing telemetry ID |
| `vehicle_id` | VARCHAR(36) | FOREIGN KEY (vehicles.id) INDEX | Associated vehicle |
| `latitude` | DOUBLE PRECISION | NOT NULL | WGS84 Latitude (-90 to +90) |
| `longitude` | DOUBLE PRECISION | NOT NULL | WGS84 Longitude (-180 to +180) |
| `altitude` | FLOAT | NULL | Altitude above sea level in meters |
| `speed_kmh` | FLOAT | NOT NULL, DEFAULT 0.0 | Instantaneous speed (km/h) |
| `heading` | FLOAT | DEFAULT 0.0 | Compass orientation (0 - 359 degrees) |
| `satellites` | INTEGER | DEFAULT 8 | Satellites locked |
| `ignition` | BOOLEAN | DEFAULT TRUE | Engine ignition state |
| `battery_pct` | FLOAT | DEFAULT 100.0 | Tracker internal backup battery % |
| `fuel_level_pct`| FLOAT | NULL | Current fuel sensor reading % |
| `odometer_km` | FLOAT | NULL | Cumulative odometer reading |
| `recorded_at` | TIMESTAMPTZ | NOT NULL, INDEX | Hardware timestamp of reading |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Server ingestion timestamp |

**Recommended Indexes**:
- `CREATE INDEX idx_telemetry_vehicle_time ON gps_telemetry (vehicle_id, recorded_at DESC);`
- `CREATE INDEX idx_telemetry_time ON gps_telemetry (recorded_at DESC);`

---

## 6. `geofences`
Virtual geographical boundaries for perimeter monitoring.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Geofence identifier |
| `organization_id`| VARCHAR(36) | FOREIGN KEY (organizations.id) | Tenant reference |
| `name` | VARCHAR(100) | NOT NULL | Zone name (e.g. City Depot) |
| `fence_type` | VARCHAR(20) | NOT NULL | `circle` or `polygon` |
| `center_latitude`| DOUBLE PRECISION | NULL | Center latitude (for circular fences) |
| `center_longitude`| DOUBLE PRECISION | NULL | Center longitude (for circular fences) |
| `radius_meters` | FLOAT | NULL | Radius in meters (for circular fences) |
| `coordinates_json`| JSONB / TEXT | NULL | GeoJSON array of `[[lat, lng], ...]` |
| `alert_on_entry` | BOOLEAN | DEFAULT TRUE | Trigger alert upon entering |
| `alert_on_exit` | BOOLEAN | DEFAULT TRUE | Trigger alert upon exiting |
| `color_hex` | VARCHAR(10) | DEFAULT '#3B82F6' | Map rendering polygon color |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Created timestamp |

---

## 7. `alerts`
Events generated by telemetry rules (overspeed, geofence, hardware SOS).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Alert identifier |
| `vehicle_id` | VARCHAR(36) | FOREIGN KEY (vehicles.id) INDEX | Triggering vehicle |
| `geofence_id` | VARCHAR(36) | FOREIGN KEY (geofences.id) NULL | Related geofence |
| `alert_type` | VARCHAR(30) | NOT NULL | `overspeed`, `geofence_entry`, `geofence_exit`, `sos`, `low_battery` |
| `severity` | VARCHAR(15) | NOT NULL, DEFAULT 'warning' | `info`, `warning`, `critical` |
| `message` | VARCHAR(255) | NOT NULL | Human-readable alert summary |
| `latitude` | DOUBLE PRECISION | NULL | Latitude where event triggered |
| `longitude` | DOUBLE PRECISION | NULL | Longitude where event triggered |
| `speed_kmh` | FLOAT | NULL | Vehicle speed at trigger moment |
| `is_acknowledged`| BOOLEAN | DEFAULT FALSE | Operator acknowledgment flag |
| `acknowledged_by`| VARCHAR(36) | FOREIGN KEY (users.id) NULL | User who dismissed alert |
| `acknowledged_at`| TIMESTAMPTZ | NULL | Dismissal timestamp |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Alert timestamp |

---

## 8. `trips`
Calculated travel segments with summary statistics.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Trip identifier |
| `vehicle_id` | VARCHAR(36) | FOREIGN KEY (vehicles.id) INDEX | Associated vehicle |
| `driver_id` | VARCHAR(36) | FOREIGN KEY (drivers.id) NULL | Active driver during trip |
| `start_time` | TIMESTAMPTZ | NOT NULL | Trip commencement |
| `end_time` | TIMESTAMPTZ | NULL | Trip completion |
| `start_latitude`| DOUBLE PRECISION | NOT NULL | Departure latitude |
| `start_longitude`| DOUBLE PRECISION| NOT NULL | Departure longitude |
| `end_latitude` | DOUBLE PRECISION | NULL | Arrival latitude |
| `end_longitude` | DOUBLE PRECISION | NULL | Arrival longitude |
| `distance_km` | FLOAT | DEFAULT 0.0 | Total travel distance |
| `duration_minutes`| FLOAT | DEFAULT 0.0 | Elapsed travel duration |
| `max_speed_kmh` | FLOAT | DEFAULT 0.0 | Maximum recorded speed |
| `avg_speed_kmh` | FLOAT | DEFAULT 0.0 | Mean running speed |
| `status` | VARCHAR(20) | DEFAULT 'in_progress' | `in_progress`, `completed`, `cancelled` |
| `load_status` | VARCHAR(20) | DEFAULT 'empty' | `loaded` or `empty` cargo payload state |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |

---

## 9. `stops`
Detected stopping periods during journeys.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Stop identifier |
| `trip_id` | VARCHAR(36) | FOREIGN KEY (trips.id) INDEX | Associated journey |
| `latitude` | DOUBLE PRECISION | NOT NULL | Stop coordinate |
| `longitude` | DOUBLE PRECISION | NOT NULL | Stop coordinate |
| `address` | VARCHAR(255) | NULL | Reverse-geocoded address |
| `arrived_at` | TIMESTAMPTZ | NOT NULL | Stop arrival time |
| `departed_at`| TIMESTAMPTZ | NULL | Resumed travel time |
| `duration_minutes` | FLOAT | DEFAULT 0.0 | Total stop duration |
| `is_idle` | BOOLEAN | DEFAULT TRUE | Engine idling during stop |

---

## 10. `trip_events`
Discrete incident markers along a vehicle route.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Event ID |
| `trip_id` | VARCHAR(36) | FOREIGN KEY (trips.id) INDEX | Associated trip |
| `event_type` | VARCHAR(40) | NOT NULL | `trip_start`, `trip_end`, `overspeed`, `harsh_brake`, `sos` |
| `latitude` | DOUBLE PRECISION | NULL | Event position |
| `longitude` | DOUBLE PRECISION | NULL | Event position |
| `speed_kmh` | FLOAT | NULL | Speed at event time |
| `description`| VARCHAR(255) | NULL | Incident notes |
| `occurred_at`| TIMESTAMPTZ | NOT NULL | Event timestamp |

---

## 11. `gps_devices`
Physical tracking hardware bound to commercial vehicles.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | VARCHAR(36) | PRIMARY KEY | Tracker ID |
| `vehicle_id` | VARCHAR(36) | FOREIGN KEY (vehicles.id) UNIQUE | Bound truck |
| `imei` | VARCHAR(30) | UNIQUE, NOT NULL | 15-digit device IMEI |
| `manufacturer`| VARCHAR(60) | NULL | e.g. Teltonika, Concox, Queclink |
| `model` | VARCHAR(60) | NULL | Hardware device model |
| `status` | VARCHAR(20) | DEFAULT 'active' | `active`, `inactive`, `decommissioned` |

---

## 12. `companies` & `company_locations`
Freight customers and delivery / pickup warehouse sites.

| Table | Column | Type | Description |
| :--- | :--- | :--- | :--- |
| `companies` | `name` | VARCHAR(120) | Customer company name |
| `companies` | `gst_number` | VARCHAR(30) | Tax registration identification |
| `company_locations` | `company_id` | VARCHAR(36) | Parent company reference |
| `company_locations` | `location_type` | VARCHAR(30) | `warehouse`, `depot`, `port`, `office` |
| `company_locations` | `geofence_id` | VARCHAR(36) | Optional perimeter boundary reference |

---

## 13. `maintenance_logs` & `fuel_logs`
Scheduled vehicle servicing and refueling transactions.

