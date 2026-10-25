/**
 * Real-time GPS Tracking page logic with live Leaflet map, geofence layers,
 * fleet filtering, and real-time Telemetry Simulator.
 */
let fleetMapInstance = null;
let pollTimer = null;
let allLiveVehicles = [];
let selectedVehicleId = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  fleetMapInstance = new FleetMap('fleet-map');

  // Check URL query param for focused vehicle
  const urlParams = new URLSearchParams(window.location.search);
  selectedVehicleId = urlParams.get('focus');

  // Load geofences onto map
  await loadGeofences();

  // Initial live vehicle fetch
  await fetchLivePositions();

  // Setup search & filter listeners
  setupFilters();

  // Telemetry simulator modal setup
  setupSimulator();

  // Start continuous polling (every 4s)
  pollTimer = setInterval(fetchLivePositions, CONFIG.POLL_INTERVAL_MS);
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

async function loadGeofences() {
  try {
    const fencesRes = await ApiClient.get('/geofences');
    if (fencesRes.success && fencesRes.data) {
      fleetMapInstance.renderGeofences(fencesRes.data);
    }
  } catch (err) {
    console.error('Failed to load geofences onto map:', err);
  }
}

async function fetchLivePositions() {
  try {
    const res = await ApiClient.get('/gps/live');
    if (res.success && Array.isArray(res.data)) {
      allLiveVehicles = res.data;
      filterAndRenderVehicles();

      // If a vehicle was requested to be focused on initial load
      if (selectedVehicleId) {
        const target = allLiveVehicles.find(v => v.vehicle_id === selectedVehicleId);
        if (target && target.latitude && target.longitude) {
          focusVehicle(target.vehicle_id, target.latitude, target.longitude);
          selectedVehicleId = null; // focused once
        }
      }
    }
  } catch (err) {
    console.error('Error fetching live positions:', err);
  }
}

function setupFilters() {
  const searchInput = document.getElementById('vehicle-search-input');
  const statusFilter = document.getElementById('vehicle-status-filter');

  if (searchInput) {
    searchInput.addEventListener('input', () => filterAndRenderVehicles());
  }
  if (statusFilter) {
    statusFilter.addEventListener('change', () => filterAndRenderVehicles());
  }
}

function filterAndRenderVehicles() {
  const searchInput = document.getElementById('vehicle-search-input');
  const statusFilter = document.getElementById('vehicle-status-filter');

  const searchTerm = searchInput ? searchInput.value.trim().toLowerCase() : '';
  const statusTerm = statusFilter ? statusFilter.value : '';

  const filtered = allLiveVehicles.filter(v => {
    const matchesSearch = !searchTerm ||
      (v.registration_number && v.registration_number.toLowerCase().includes(searchTerm)) ||
      (v.driver_name && v.driver_name.toLowerCase().includes(searchTerm));

    const matchesStatus = !statusTerm || (v.status === statusTerm);
    return matchesSearch && matchesStatus;
  });

  updateLiveFleetList(filtered);

  // Update map markers
  allLiveVehicles.forEach(v => {
    if (fleetMapInstance && v.latitude && v.longitude) {
      fleetMapInstance.updateVehicleMarker(v);
    }
  });
}

function updateLiveFleetList(vehicles) {
  const listEl = document.getElementById('live-vehicles-list');
  const countEl = document.getElementById('live-vehicles-count');

  if (countEl) countEl.textContent = `${vehicles.length} Units`;

  if (!listEl) return;

  if (vehicles.length === 0) {
    listEl.innerHTML = '<div class="text-center text-muted p-4"><i class="bi bi-truck display-6 d-block mb-2 opacity-50"></i>No matching vehicles online</div>';
    return;
  }

  listEl.innerHTML = vehicles.map(v => `
    <div class="p-3 border-bottom border-secondary border-opacity-10 vehicle-card-item cursor-pointer" 
         onclick="focusVehicle('${v.vehicle_id}', ${v.latitude}, ${v.longitude})"
         style="cursor: pointer; transition: background 0.2s;"
         onmouseover="this.style.background='rgba(255,255,255,0.03)'"
         onmouseout="this.style.background='transparent'">
      <div class="d-flex justify-content-between align-items-center mb-1">
        <span class="fw-bold text-white"><i class="bi bi-truck me-1 text-primary"></i>${v.registration_number}</span>
        ${Utils.getStatusBadge(v.status)}
      </div>
      <div class="d-flex justify-content-between text-muted small mb-1">
        <span><i class="bi bi-speedometer2 me-1"></i>${Utils.formatSpeed(v.speed_kmh)}</span>
        <span><i class="bi bi-person me-1"></i>${v.driver_name || 'Unassigned'}</span>
      </div>
      <div class="d-flex justify-content-between text-dim small">
        <span><i class="bi bi-geo-alt me-1"></i>${Number(v.latitude).toFixed(4)}, ${Number(v.longitude).toFixed(4)}</span>
        <span>${Utils.formatDate(v.last_updated)}</span>
      </div>
    </div>
  `).join('');
}

function focusVehicle(id, lat, lng) {
  if (fleetMapInstance && fleetMapInstance.map && lat && lng) {
    fleetMapInstance.map.flyTo([lat, lng], 15, { duration: 1.2 });
    const marker = fleetMapInstance.markers.get(id);
    if (marker) {
      setTimeout(() => marker.openPopup(), 600);
    }
  }
}

/**
 * Telemetry Simulator:
 * Allows dispatchers to send simulated GPS packets to test real-time movement.
 */
function setupSimulator() {
  const form = document.getElementById('telemetry-sim-form');
  const truckSelect = document.getElementById('sim-vehicle-select');

  // Populate truck selector in simulator modal
  if (truckSelect) {
    ApiClient.get('/vehicles?limit=100').then(res => {
      if (res.success && res.data) {
        truckSelect.innerHTML = res.data.map(v => `
          <option value="${v.id}">${v.registration_number} (${v.make} ${v.model})</option>
        `).join('');
      }
    }).catch(console.error);
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const vehicleId = document.getElementById('sim-vehicle-select').value;
      const lat = parseFloat(document.getElementById('sim-lat').value);
      const lng = parseFloat(document.getElementById('sim-lng').value);
      const speed = parseFloat(document.getElementById('sim-speed').value || '45');
      const heading = parseFloat(document.getElementById('sim-heading').value || '90');
      const ignition = document.getElementById('sim-ignition').checked;

      try {
        const payload = {
          vehicle_id: vehicleId,
          latitude: lat,
          longitude: lng,
          speed_kmh: speed,
          heading: heading,
          ignition: ignition,
          battery_pct: 95,
          fuel_level_pct: 82,
        };

        const res = await ApiClient.post('/gps/locations', payload);
        if (res.success) {
          Utils.showToast('Simulated GPS coordinates transmitted!', 'success');
          const modalEl = document.getElementById('simulateGpsModal');
          const modal = bootstrap.Modal.getInstance(modalEl);
          if (modal) modal.hide();

          // Immediately fetch and pan to coordinates
          await fetchLivePositions();
          focusVehicle(vehicleId, lat, lng);
        }
      } catch (err) {
        Utils.showToast(err.message || 'Simulation failed', 'danger');
      }
    });
  }
}
