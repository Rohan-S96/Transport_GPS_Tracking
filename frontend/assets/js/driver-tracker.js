/**
 * Driver Mobile GPS Tracker
 * 
 * Captures high-accuracy mobile phone GPS telemetry and streams it to the
 * backend API in real time. Designed specifically for smartphones with:
 * - HTML5 Geolocation API (watchPosition high-accuracy mode)
 * - Screen WakeLock API (prevents mobile screen sleep during transit)
 * - Battery Status API (transmits driver phone battery to dispatch)
 * - Offline Queueing & Automatic Sync upon reconnection
 * - Live Leaflet mini route preview
 */

let watchId = null;
let wakeLock = null;
let isTracking = false;

let selectedVehicle = null; // { id, registration_number, make, model }
let vehiclesList = [];

// Telemetry state
let lastPosition = null;
let totalDistanceKm = 0.0;
let packetsSentCount = 0;
let lastSentTime = 0;
const SEND_INTERVAL_MS = 3500; // Transmit coordinate every 3.5 seconds

// Mini Leaflet Map
let driverMap = null;
let driverMarker = null;
let driverRoutePolyline = null;
let routeCoordinates = [];

// Offline queue in localStorage
const OFFLINE_QUEUE_KEY = 'tgt_driver_offline_queue';

document.addEventListener('DOMContentLoaded', async () => {
  initMiniMap();
  initBatteryStatus();
  setupEventListeners();
  await loadVehicles();
  checkUrlParams();
  checkOfflineQueue();
});

// ── 1. INITIALIZE MINI LEAFLET MAP ──────────────────────────────────────────

function initMiniMap() {
  const mapEl = document.getElementById('driver-mini-map');
  if (!mapEl) return;

  const defaultCenter = [19.0760, 72.8777]; // Default Mumbai center
  driverMap = L.map('driver-mini-map', {
    zoomControl: false,
    attributionControl: false,
  }).setView(defaultCenter, 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
  }).addTo(driverMap);

  driverRoutePolyline = L.polyline([], {
    color: '#38bdf8',
    weight: 4,
    opacity: 0.85,
    lineJoin: 'round',
  }).addTo(driverMap);
}

function updateMiniMapMarker(lat, lng, heading = 0) {
  if (!driverMap) return;

  const latLng = [lat, lng];
  routeCoordinates.push(latLng);
  driverRoutePolyline.setLatLngs(routeCoordinates);

  const iconHtml = `
    <div style="transform: rotate(${heading}deg); width: 32px; height: 32px; display:flex; align-items:center; justify-content:center; background:#0284c7; border:2px solid #ffffff; border-radius:50%; box-shadow:0 0 12px #38bdf8; color:#ffffff; font-size:16px;">
      <i class="bi bi-truck-front-fill"></i>
    </div>
  `;

  const truckIcon = L.divIcon({
    className: 'driver-truck-pin',
    html: iconHtml,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  });

  if (!driverMarker) {
    driverMarker = L.marker(latLng, { icon: truckIcon }).addTo(driverMap);
    driverMap.setView(latLng, 16);
  } else {
    driverMarker.setLatLng(latLng);
    driverMarker.setIcon(truckIcon);
    driverMap.panTo(latLng);
  }
}

// ── 2. LOAD TRUCKS (PUBLIC ROSTER) ──────────────────────────────────────────

async function loadVehicles() {
  const selectEl = document.getElementById('vehicle-select');
  const hintEl = document.getElementById('vehicle-hint');

  try {
    const res = await fetch(`${CONFIG.API_BASE_URL}/vehicles/public-roster`);
    const json = await res.json();

    if (json.success && Array.isArray(json.data) && json.data.length > 0) {
      vehiclesList = json.data;
      selectEl.innerHTML = '<option value="">-- Choose Truck --</option>' +
        vehiclesList.map(v => `
          <option value="${v.registration_number}" data-id="${v.id}">
            ${v.registration_number} (${v.make} ${v.model}) ${v.driver_name ? '- ' + v.driver_name : ''}
          </option>
        `).join('');

      hintEl.textContent = `${vehiclesList.length} trucks available for mobile tracking.`;
    } else {
      hintEl.textContent = 'No active trucks found. You can enter registration manually.';
    }
  } catch (err) {
    console.warn('Failed to load public roster, falling back to manual entry:', err);
    hintEl.textContent = 'Unable to reach roster. Enter registration directly.';
  }
}

// ── 3. PARSE URL PARAMETERS (AUTO SELECTION) ────────────────────────────────

function checkUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const targetTruck = params.get('v') || params.get('truck') || params.get('reg');
  const targetId = params.get('id') || params.get('vehicle_id');
  const driverName = params.get('driver') || params.get('name');

  if (driverName) {
    const nameInput = document.getElementById('driver-name-input');
    if (nameInput) nameInput.value = driverName;
  }

  if (targetTruck) {
    const selectEl = document.getElementById('vehicle-select');
    // Try finding in select options
    let found = false;
    for (let opt of selectEl.options) {
      if (opt.value.toLowerCase() === targetTruck.trim().toLowerCase()) {
        opt.selected = true;
        found = true;
        break;
      }
    }
    // If not found in dropdown, append it
    if (!found) {
      const newOpt = new Option(`${targetTruck.toUpperCase()} (Manual)`, targetTruck.toUpperCase(), true, true);
      if (targetId) newOpt.setAttribute('data-id', targetId);
      selectEl.add(newOpt);
    }
    onVehicleSelected();
  }
}

function onVehicleSelected() {
  const selectEl = document.getElementById('vehicle-select');
  const selectedOpt = selectEl.options[selectEl.selectedIndex];

  if (selectEl.value) {
    selectedVehicle = {
      registration_number: selectEl.value,
      id: selectedOpt ? selectedOpt.getAttribute('data-id') : null,
    };
    const truckNameEl = document.getElementById('active-truck-name');
    if (truckNameEl) truckNameEl.textContent = selectedVehicle.registration_number;
  } else {
    selectedVehicle = null;
  }
}

// ── 4. EVENT LISTENERS & TRACKING TOGGLE ────────────────────────────────────

function setupEventListeners() {
  const selectEl = document.getElementById('vehicle-select');
  if (selectEl) {
    selectEl.addEventListener('change', onVehicleSelected);
  }

  const toggleBtn = document.getElementById('btn-toggle-tracking');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      if (isTracking) {
        stopTracking();
      } else {
        startTracking();
      }
    });
  }

  const recenterBtn = document.getElementById('btn-recenter-map');
  if (recenterBtn) {
    recenterBtn.addEventListener('click', () => {
      if (driverMarker && driverMap) {
        driverMap.setView(driverMarker.getLatLng(), 16);
      }
    });
  }

  // Handle visibility changes to maintain Screen WakeLock
  document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'visible' && isTracking) {
      await requestWakeLock();
    }
  });

  // Online / Offline window events
  window.addEventListener('online', () => {
    updateNetworkStatus(true);
    checkOfflineQueue();
  });
  window.addEventListener('offline', () => {
    updateNetworkStatus(false);
  });
}

// ── 5. START / STOP GPS TRACKING ────────────────────────────────────────────

async function startTracking() {
  const selectEl = document.getElementById('vehicle-select');
  if (!selectEl || !selectEl.value) {
    Utils.showToast('Please select or enter a truck registration number first!', 'warning');
    selectEl.focus();
    return;
  }

  onVehicleSelected();

  if (!('geolocation' in navigator)) {
    Utils.showToast('Geolocation is not supported by your mobile browser.', 'danger');
    return;
  }

  // Request WakeLock to prevent phone display sleep
  await requestWakeLock();

  // Reset metrics
  totalDistanceKm = 0.0;
  packetsSentCount = 0;
  routeCoordinates = [];
  lastPosition = null;

  updateTrackingUI(true);

  // Watch position with highest possible accuracy
  const geoOptions = {
    enableHighAccuracy: true,
    timeout: 15000,
    maximumAge: 0,
  };

  watchId = navigator.geolocation.watchPosition(
    onLocationSuccess,
    onLocationError,
    geoOptions
  );

  isTracking = true;
  Utils.showToast(`GPS Tracking started for ${selectedVehicle.registration_number}!`, 'success');
}

function stopTracking() {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }

  releaseWakeLock();
  isTracking = false;
  updateTrackingUI(false);

  Utils.showToast(`Tracking stopped. Total distance: ${totalDistanceKm.toFixed(2)} km. Sent: ${packetsSentCount} packets.`, 'info');
}

function updateTrackingUI(active) {
  const btn = document.getElementById('btn-toggle-tracking');
  const badge = document.getElementById('status-pulse-dot');
  const netText = document.getElementById('network-status-text');
  const activeBadge = document.getElementById('tracking-active-badge');

  if (active) {
    btn.className = 'btn btn-danger btn-track-action w-100 d-flex align-items-center justify-content-center gap-2';
    btn.innerHTML = '<i class="bi bi-stop-circle-fill fs-4"></i><span>STOP TRACKING</span>';
    badge.className = 'pulse-dot tracking';
    netText.textContent = 'Transmitting';
    if (activeBadge) activeBadge.style.display = 'inline-block';
  } else {
    btn.className = 'btn btn-success btn-track-action w-100 d-flex align-items-center justify-content-center gap-2';
    btn.innerHTML = '<i class="bi bi-play-circle-fill fs-4"></i><span>START GPS TRACKING</span>';
    badge.className = 'pulse-dot online';
    netText.textContent = 'Ready';
    if (activeBadge) activeBadge.style.display = 'none';

    document.getElementById('metric-speed').textContent = '0';
  }
}

// ── 6. GEOLOCATION HANDLERS ─────────────────────────────────────────────────

function onLocationSuccess(position) {
  const coords = position.coords;
  const lat = coords.latitude;
  const lng = coords.longitude;
  const accuracy = coords.accuracy || 10;
  let speedKmh = coords.speed !== null && !isNaN(coords.speed) ? (coords.speed * 3.6) : 0.0;
  const heading = coords.heading !== null && !isNaN(coords.heading) ? coords.heading : 0.0;
  const altitude = coords.altitude !== null && !isNaN(coords.altitude) ? coords.altitude : null;

  // Compute odometer distance from previous point
  if (lastPosition) {
    const deltaKm = calculateDistanceKm(
      lastPosition.latitude, lastPosition.longitude,
      lat, lng
    );
    // Filter micro-jitter (< 4 meters)
    if (deltaKm > 0.004) {
      totalDistanceKm += deltaKm;
      // If hardware speed wasn't reported, compute derived speed
      if (speedKmh <= 0.5) {
        const timeDiffHours = (position.timestamp - lastPosition.timestamp) / (1000 * 3600);
        if (timeDiffHours > 0) {
          const derivedSpeed = deltaKm / timeDiffHours;
          if (derivedSpeed < 140) speedKmh = derivedSpeed;
        }
      }
    }
  }

  lastPosition = {
    latitude: lat,
    longitude: lng,
    timestamp: position.timestamp,
  };

  // Update Driver Dashboard metrics
  updateCockpitMetrics(lat, lng, speedKmh, heading, accuracy);

  // Update Mini Map
  updateMiniMapMarker(lat, lng, heading);

  // Rate-limit transmission to every 3.5 seconds
  const now = Date.now();
  if (now - lastSentTime >= SEND_INTERVAL_MS) {
    lastSentTime = now;
    sendTelemetryPacket({
      latitude: lat,
      longitude: lng,
      speed_kmh: Math.round(speedKmh * 10) / 10,
      heading: Math.round(heading),
      altitude: altitude ? Math.round(altitude) : null,
      accuracy_m: Math.round(accuracy),
      ignition: speedKmh > 2.0,
      timestamp: new Date().toISOString(),
    });
  }
}

function onLocationError(err) {
  console.warn('Geolocation error:', err);
  let msg = 'GPS Signal error';
  switch (err.code) {
    case err.PERMISSION_DENIED:
      msg = 'Location permission denied. Please allow GPS access in your browser.';
      stopTracking();
      break;
    case err.POSITION_UNAVAILABLE:
      msg = 'GPS signal unavailable. Ensure Location is turned ON on your phone.';
      break;
    case err.TIMEOUT:
      msg = 'GPS request timed out. Searching for satellites...';
      break;
  }
  Utils.showToast(msg, 'warning');
}

// ── 7. TRANSMIT TELEMETRY TO BACKEND ─────────────────────────────────────────

async function sendTelemetryPacket(telemetryData) {
  if (!selectedVehicle) return;

  const batteryPct = await getBatteryPercentage();

  const payload = {
    registration_number: selectedVehicle.registration_number,
    vehicle_id: selectedVehicle.id || undefined,
    latitude: telemetryData.latitude,
    longitude: telemetryData.longitude,
    speed_kmh: telemetryData.speed_kmh,
    heading: telemetryData.heading,
    altitude: telemetryData.altitude,
    battery_pct: batteryPct,
    ignition: telemetryData.ignition,
    source: 'mobile_phone',
    timestamp: telemetryData.timestamp,
  };

  try {
    const res = await fetch(`${CONFIG.API_BASE_URL}/gps/locations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (res.ok) {
      packetsSentCount++;
      document.getElementById('metric-packets').textContent = `${packetsSentCount} pkts`;
      document.getElementById('metric-last-ping').textContent = new Date().toLocaleTimeString();
    } else {
      // Buffer packet in offline queue if server returned error
      queueOfflinePacket(payload);
    }
  } catch (netErr) {
    console.warn('Network offline or packet failed, queueing locally:', netErr);
    queueOfflinePacket(payload);
  }
}

// ── 8. OFFLINE QUEUE RESILIENCE ─────────────────────────────────────────────

function queueOfflinePacket(packet) {
  try {
    const queue = JSON.parse(localStorage.getItem(OFFLINE_QUEUE_KEY) || '[]');
    if (queue.length > 200) queue.shift(); // Keep last 200 packets to conserve storage
    queue.push(packet);
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
    document.getElementById('metric-last-ping').textContent = `Queued (${queue.length})`;
  } catch (e) {
    console.error('Failed to write to offline queue:', e);
  }
}

async function checkOfflineQueue() {
  const queueJson = localStorage.getItem(OFFLINE_QUEUE_KEY);
  if (!queueJson) return;

  try {
    const queue = JSON.parse(queueJson);
    if (!Array.isArray(queue) || queue.length === 0) return;

    console.log(`Flushing ${queue.length} offline GPS packets...`);
    while (queue.length > 0) {
      const packet = queue.shift();
      try {
        await fetch(`${CONFIG.API_BASE_URL}/gps/locations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(packet),
        });
        packetsSentCount++;
      } catch (err) {
        // Still offline, push back and break
        queue.unshift(packet);
        break;
      }
    }
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(queue));
    document.getElementById('metric-packets').textContent = `${packetsSentCount} pkts`;
  } catch (e) {
    console.error('Error syncing offline queue:', e);
  }
}

// ── 9. DASHBOARD METRICS DISPLAY ────────────────────────────────────────────

function updateCockpitMetrics(lat, lng, speedKmh, heading, accuracy) {
  // Speed
  const speedEl = document.getElementById('metric-speed');
  if (speedEl) {
    const speedVal = Math.round(speedKmh);
    speedEl.textContent = speedVal;
    if (speedVal > 80) {
      speedEl.style.color = '#ef4444'; // Overspeed red
    } else if (speedVal > 60) {
      speedEl.style.color = '#f59e0b'; // Warning amber
    } else {
      speedEl.style.color = '#38bdf8'; // Normal cyan
    }
  }

  // Distance
  const distEl = document.getElementById('metric-distance');
  if (distEl) distEl.textContent = `${totalDistanceKm.toFixed(2)} km`;

  // Accuracy
  const accEl = document.getElementById('metric-accuracy');
  if (accEl) {
    accEl.textContent = `\u00B1 ${Math.round(accuracy)} m`;
    if (accuracy <= 10) {
      accEl.className = 'mini-metric-val text-success';
    } else if (accuracy <= 25) {
      accEl.className = 'mini-metric-val text-warning';
    } else {
      accEl.className = 'mini-metric-val text-danger';
    }
  }

  // Heading
  const headEl = document.getElementById('metric-heading');
  if (headEl) {
    const compassDir = headingToCompass(heading);
    headEl.textContent = `${Math.round(heading)}\u00B0 ${compassDir}`;
  }

  // Coordinates
  const coordsEl = document.getElementById('metric-coords');
  if (coordsEl) {
    coordsEl.textContent = `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
  }
}

function updateNetworkStatus(online) {
  const badge = document.getElementById('status-pulse-dot');
  const netText = document.getElementById('network-status-text');
  if (online) {
    badge.className = isTracking ? 'pulse-dot tracking' : 'pulse-dot online';
    netText.textContent = isTracking ? 'Transmitting' : 'Ready';
  } else {
    badge.className = 'pulse-dot offline';
    netText.textContent = 'Offline (Buffering)';
  }
}

// ── 10. SCREEN WAKELOCK & BATTERY HELPERS ────────────────────────────────────

async function requestWakeLock() {
  if ('wakeLock' in navigator) {
    try {
      wakeLock = await navigator.wakeLock.request('screen');
      wakeLock.addEventListener('release', () => {
        wakeLock = null;
      });
    } catch (err) {
      console.warn('WakeLock could not be obtained:', err);
    }
  }
}

function releaseWakeLock() {
  if (wakeLock !== null) {
    wakeLock.release().catch(console.warn);
    wakeLock = null;
  }
}

async function initBatteryStatus() {
  const batteryEl = document.getElementById('metric-battery');
  if (!batteryEl) return;

  const pct = await getBatteryPercentage();
  if (pct !== null) {
    batteryEl.innerHTML = `<i class="bi bi-battery-charging text-success me-1"></i>${pct}%`;
  }
}

async function getBatteryPercentage() {
  if ('getBattery' in navigator) {
    try {
      const battery = await navigator.getBattery();
      return Math.round(battery.level * 100);
    } catch (e) {
      return 100;
    }
  }
  return 100;
}

// ── 11. GEO UTILITIES ───────────────────────────────────────────────────────

function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function headingToCompass(deg) {
  if (deg === null || isNaN(deg)) return '';
  const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  const index = Math.round(((deg %= 360) < 0 ? deg + 360 : deg) / 45) % 8;
  return directions[index];
}
