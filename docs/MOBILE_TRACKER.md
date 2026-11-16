# 📱 Driver Mobile GPS Tracker: Technical Specification & Guide

The **Driver Mobile GPS Tracker** (`frontend/driver-tracker.html`) transforms any standard smartphone (iOS Safari, Android Chrome/Firefox) into a professional-grade fleet tracking device without requiring drivers to download or install proprietary native apps from app stores.

---

## 1. Web Capabilities & Modern APIs

| API | Implementation Detail | Operational Benefit |
| :--- | :--- | :--- |
| **HTML5 Geolocation API** | Continuous `navigator.geolocation.watchPosition` with `enableHighAccuracy: true`, `maximumAge: 0`. | Millimeter-accurate positioning using GPS, GLONASS, Galileo, and cellular tower trilateration. |
| **Screen WakeLock API** | `navigator.wakeLock.request('screen')` automatically re-acquired on visibility change. | Keeps the smartphone display awake during transit, preventing aggressive OS background CPU suspension. |
| **Battery Status API** | `navigator.getBattery()` streams current battery percentage and charging state. | Allows dispatchers to monitor low driver phone batteries before a signal loss occurs. |
| **Navigator `sendBeacon`** | Sends `POST /api/v1/gps/disconnect` on `pagehide` and `beforeunload`. | Guaranteed delivery of offline signal even when drivers swipe-close their mobile browser tab. |
| **LocalStorage Queue** | Serializes pending coordinates if cellular connection drops (`window.onoffline`). | Zero data loss when trucks traverse mountain tunnels, valleys, or poor coverage zones. |

---

## 2. Instant Truck Pairing via URL / QR Code

Drivers can pair their smartphone with a truck in seconds without logging into an administrative account.

### URL Structure
```
https://<domain>/driver-tracker.html?v=<REGISTRATION_NUMBER>&driver=<DRIVER_NAME>
```

**Example**:
```
https://transportgpstracking-frontend.vercel.app/driver-tracker.html?v=MH-04-AB-1234&driver=Rohan+Saste
```

When opened:
1. The web app queries the public roster endpoint `GET /api/v1/vehicles/public-roster`.
2. Automatically pre-selects the truck in the dropdown.
3. Automatically populates the driver name field.
4. Highlights the green **START GPS TRACKING** button for 1-tap activation.

---

## 3. Communication Protocol

### Step 1: Online Connection Handshake
When the driver taps **START GPS TRACKING**:
- Client sends: `POST /api/v1/gps/connect` with `{ "registration_number": "MH-04-AB-1234" }`
- Backend immediately updates `vehicle.status = "active"` and `vehicle.updated_at = NOW()`.
- Dispatch radar immediately switches the truck indicator from <span style="color:#6b7280;">Offline</span> to <span style="color:#22c55e;">Online (Live)</span>.

### Step 2: High-Frequency Telemetry Stream
Every $3.5\text{ seconds}$ (or immediately when heading changes by $\ge 15^\circ$):
- Client streams coordinate packet to `POST /api/v1/gps/locations`:
  ```json
  {
    "registration_number": "MH-04-AB-1234",
    "latitude": 19.0388,
    "longitude": 73.0302,
    "speed_kmh": 42.1,
    "heading": 182.0,
    "battery_pct": 85.0,
    "ignition": true,
    "timestamp": "2026-11-16T08:45:00.000Z"
  }
  ```

### Step 3: Clean Disconnection
When the driver taps **STOP TRACKING** or closes the browser tab:
- Client fires `POST /api/v1/gps/disconnect`.
- Backend marks `vehicle.status = "offline"`.
- Dispatch radar instantly reflects disconnected state.

---

## 4. Mobile Troubleshooting Guide for Drivers

### 1. "Geolocation Permission Denied"
- **iOS (Safari)**: Settings $\to$ Privacy & Security $\to$ Location Services $\to$ Safari Websites $\to$ Select "While Using the App" and toggle "Precise Location" **ON**.
- **Android (Chrome)**: Tap lock icon next to URL $\to$ Permissions $\to$ Location $\to$ Allow.

### 2. "Transmitting Pauses When Screen Turns Off"
- Ensure you have granted permission for the browser to stay active.
- Connect the smartphone to the vehicle's dashboard 12V USB charger.
- The web app automatically activates the Screen WakeLock API to keep the phone screen active throughout the journey.
