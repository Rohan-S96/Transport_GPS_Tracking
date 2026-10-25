/**
 * Historical Route Playback, Waypoint Scrubber, and Speed Simulation HUD.
 */
let playbackMap = null;
let waypoints = [];
let currentIndex = 0;
let isPlaying = false;
let playInterval = null;
let playSpeed = 1; // 1x, 2x, 5x, 10x

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  playbackMap = new FleetMap('playback-map');

  await loadTripAndVehicleOptions();

  // If trip_id or vehicle_id passed in query string
  const urlParams = new URLSearchParams(window.location.search);
  const tripIdParam = urlParams.get('trip_id');
  const vehicleIdParam = urlParams.get('vehicle_id');

  if (tripIdParam) {
    document.getElementById('playback-trip-select').value = tripIdParam;
    loadTripRoute(tripIdParam);
  } else if (vehicleIdParam) {
    document.getElementById('playback-vehicle-select').value = vehicleIdParam;
    loadVehicleHistory(vehicleIdParam);
  }

  setupPlaybackControls();
});

function setupMobileSidebar() {
  const toggleBtn = document.getElementById('sidebar-toggle-btn');
  const sidebar = document.querySelector('.app-sidebar');
  const overlay = document.querySelector('.sidebar-overlay');
  if (toggleBtn && sidebar && overlay) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('show');
      overlay.classList.toggle('show');
    });
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('show');
      overlay.classList.remove('show');
    });
  }
}

async function loadTripAndVehicleOptions() {
  try {
    const [tripsRes, vehRes] = await Promise.all([
      ApiClient.get('/trips?limit=50'),
      ApiClient.get('/vehicles?limit=50'),
    ]);

    const tripSelect = document.getElementById('playback-trip-select');
    const vehSelect = document.getElementById('playback-vehicle-select');

    if (tripSelect && tripsRes.success && Array.isArray(tripsRes.data)) {
      tripSelect.innerHTML = [
        '<option value="">-- Select Completed/Active Trip --</option>',
        ...tripsRes.data.map(t => `<option value="${t.id}">${t.registration_number || 'Truck'} - ${Utils.formatDate(t.start_time)} (${Utils.formatDistance(t.distance_km)})</option>`)
      ].join('');
    }

    if (vehSelect && vehRes.success && Array.isArray(vehRes.data)) {
      vehSelect.innerHTML = [
        '<option value="">-- Or Select Vehicle --</option>',
        ...vehRes.data.map(v => `<option value="${v.id}">${v.registration_number} (${v.make} ${v.model})</option>`)
      ].join('');
    }
  } catch (err) {
    console.error('Failed to populate playback selectors:', err);
  }
}

function setupPlaybackControls() {
  const tripSelect = document.getElementById('playback-trip-select');
  const vehSelect = document.getElementById('playback-vehicle-select');
  const playBtn = document.getElementById('btn-play-pause');
  const scrubber = document.getElementById('playback-scrubber');
  const speedSelect = document.getElementById('playback-speed-select');

  if (tripSelect) {
    tripSelect.addEventListener('change', () => {
      if (tripSelect.value) {
        if (vehSelect) vehSelect.value = '';
        loadTripRoute(tripSelect.value);
      }
    });
  }

  if (vehSelect) {
    vehSelect.addEventListener('change', () => {
      if (vehSelect.value) {
        if (tripSelect) tripSelect.value = '';
        loadVehicleHistory(vehSelect.value);
      }
    });
  }

  if (playBtn) {
    playBtn.addEventListener('click', togglePlay);
  }

  if (scrubber) {
    scrubber.addEventListener('input', (e) => {
      currentIndex = parseInt(e.target.value);
      renderWaypoint(currentIndex);
    });
  }

  if (speedSelect) {
    speedSelect.addEventListener('change', (e) => {
      playSpeed = parseFloat(e.target.value) || 1;
      if (isPlaying) {
        pause();
        play();
      }
    });
  }
}

async function loadTripRoute(tripId) {
  pause();
  Utils.showToast('Fetching route waypoints...', 'info');

  try {
    const res = await ApiClient.get(`/trips/${tripId}/playback`);
    if (res.success && res.data) {
      waypoints = res.data.waypoints || [];
      const stops = (res.data.trip && res.data.trip.stops) ? res.data.trip.stops : [];

      if (waypoints.length === 0) {
        Utils.showToast('No GPS waypoints recorded for this trip segment', 'warning');
        return;
      }

      playbackMap.drawRouteHistory(waypoints, stops);
      initScrubber();
      renderWaypoint(0);
      Utils.showToast(`Loaded ${waypoints.length} route coordinates`, 'success');
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to load trip route', 'danger');
  }
}

async function loadVehicleHistory(vehicleId) {
  pause();
  Utils.showToast('Fetching vehicle history trail...', 'info');

  try {
    const res = await ApiClient.get(`/trucks/${vehicleId}/gps-history?limit=1000`);
    if (res.success && Array.isArray(res.data)) {
      waypoints = res.data;

      if (waypoints.length === 0) {
        Utils.showToast('No GPS history found for this vehicle', 'warning');
        return;
      }

      playbackMap.drawRouteHistory(waypoints, []);
      initScrubber();
      renderWaypoint(0);
      Utils.showToast(`Loaded ${waypoints.length} history coordinates`, 'success');
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to load vehicle GPS history', 'danger');
  }
}

function initScrubber() {
  const scrubber = document.getElementById('playback-scrubber');
  if (scrubber) {
    scrubber.min = 0;
    scrubber.max = Math.max(0, waypoints.length - 1);
    scrubber.value = 0;
  }
  currentIndex = 0;
}

function togglePlay() {
  if (isPlaying) {
    pause();
  } else {
    play();
  }
}

function play() {
  if (waypoints.length === 0) return;
  if (currentIndex >= waypoints.length - 1) {
    currentIndex = 0;
  }

  isPlaying = true;
  updatePlayButtonUI();

  const intervalMs = Math.max(100, 1000 / playSpeed);
  playInterval = setInterval(() => {
    if (currentIndex >= waypoints.length - 1) {
      pause();
      return;
    }
    currentIndex++;
    renderWaypoint(currentIndex);
    const scrubber = document.getElementById('playback-scrubber');
    if (scrubber) scrubber.value = currentIndex;
  }, intervalMs);
}

function pause() {
  isPlaying = false;
  clearInterval(playInterval);
  updatePlayButtonUI();
}

function updatePlayButtonUI() {
  const playBtn = document.getElementById('btn-play-pause');
  if (playBtn) {
    playBtn.innerHTML = isPlaying
      ? '<i class="bi bi-pause-fill fs-5"></i>'
      : '<i class="bi bi-play-fill fs-5"></i>';
    playBtn.className = isPlaying ? 'btn btn-warning px-4' : 'btn btn-primary px-4';
  }
}

function renderWaypoint(index) {
  if (!waypoints[index]) return;
  const pt = waypoints[index];

  // Update map marker
  playbackMap.updatePlaybackPosition(
    pt.latitude,
    pt.longitude,
    pt.heading || 0,
    pt.speed_kmh || 0,
    pt.recorded_at || pt.timestamp
  );

  // Update HUD
  const hudSpeed = document.getElementById('hud-speed');
  const hudTime = document.getElementById('hud-timestamp');
  const hudCoords = document.getElementById('hud-coords');
  const hudProgress = document.getElementById('hud-progress');

  if (hudSpeed) hudSpeed.textContent = Utils.formatSpeed(pt.speed_kmh);
  if (hudTime) hudTime.textContent = Utils.formatDate(pt.recorded_at || pt.timestamp);
  if (hudCoords) hudCoords.textContent = `${Number(pt.latitude).toFixed(5)}, ${Number(pt.longitude).toFixed(5)}`;
  if (hudProgress) hudProgress.textContent = `${index + 1} / ${waypoints.length}`;
}
