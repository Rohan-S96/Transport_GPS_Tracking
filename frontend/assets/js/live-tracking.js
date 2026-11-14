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

  // Mobile phone tracker modal setup
  setupMobileTrackModal();

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
        <div class="d-flex align-items-center gap-1">
          <span class="badge ${v.tracking_source === 'hardware_gps' ? 'bg-primary' : 'bg-success'} bg-opacity-20 ${v.tracking_source === 'hardware_gps' ? 'text-info' : 'text-success'}" style="font-size: 0.65rem;">
            ${v.tracking_source === 'hardware_gps' ? '<i class="bi bi-cpu"></i> GPS Kit' : '<i class="bi bi-phone"></i> Phone'}
          </span>
          ${Utils.getStatusBadge(v.status)}
        </div>
      </div>
      <div class="d-flex justify-content-between text-muted small mb-1">
        <span><i class="bi bi-speedometer2 me-1"></i>${Utils.formatSpeed(v.speed_kmh)}</span>
        <span><i class="bi bi-person me-1"></i>${v.driver_name || 'Unassigned'}</span>
      </div>
      <div class="d-flex justify-content-between align-items-center text-dim small">
        <span><i class="bi bi-geo-alt me-1"></i>${v.latitude ? Number(v.latitude).toFixed(4) + ', ' + Number(v.longitude).toFixed(4) : 'No coordinates yet'}</span>
        <button class="btn btn-xs btn-outline-success py-0 px-1" style="font-size: 0.7rem;" 
                onclick="event.stopPropagation(); openMobileModalForTruck('${v.registration_number}')" 
                title="Connect Driver Mobile Phone">
          <i class="bi bi-phone"></i> Track
        </button>
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

/**
 * Mobile Phone Tracking Modal:
 * Generates direct driver tracking links and live QR codes for drivers to scan.
 */
function setupMobileTrackModal() {
  const truckSelect = document.getElementById('modal-phone-truck-select');
  const linkInput = document.getElementById('modal-phone-link-input');
  const copyBtn = document.getElementById('btn-copy-driver-link');
  const whatsappBtn = document.getElementById('btn-whatsapp-share');
  const openTabBtn = document.getElementById('btn-open-driver-tab');

  if (!truckSelect) return;

  // Populate truck select from allLiveVehicles or API
  ApiClient.get('/vehicles?limit=100').then(res => {
    if (res.success && res.data) {
      truckSelect.innerHTML = '<option value="">-- Choose Truck --</option>' + res.data.map(v => `
        <option value="${v.registration_number}">
          ${v.registration_number} (${v.make} ${v.model}) ${v.assigned_driver ? '- ' + v.assigned_driver.name : ''}
        </option>
      `).join('');

      // Auto-select first vehicle
      if (res.data.length > 0) {
        truckSelect.value = res.data[0].registration_number;
        updateMobileTrackLink();
      }
    }
  }).catch(console.error);

  truckSelect.addEventListener('change', updateMobileTrackLink);

  if (copyBtn && linkInput) {
    copyBtn.addEventListener('click', () => {
      if (!linkInput.value) return;
      navigator.clipboard.writeText(linkInput.value).then(() => {
        Utils.showToast('Driver tracking link copied to clipboard!', 'success');
      }).catch(() => {
        linkInput.select();
        document.execCommand('copy');
        Utils.showToast('Link copied!', 'success');
      });
    });
  }
}

function updateMobileTrackLink() {
  const truckSelect = document.getElementById('modal-phone-truck-select');
  const linkInput = document.getElementById('modal-phone-link-input');
  const whatsappBtn = document.getElementById('btn-whatsapp-share');
  const openTabBtn = document.getElementById('btn-open-driver-tab');
  const canvas = document.getElementById('modal-phone-qrcode-canvas');

  if (!truckSelect || !linkInput) return;

  const reg = truckSelect.value.trim();
  const origin = window.location.origin;
  const driverUrl = reg
    ? `${origin}/driver-tracker.html?v=${encodeURIComponent(reg)}`
    : `${origin}/driver-tracker.html`;

  linkInput.value = driverUrl;

  if (openTabBtn) openTabBtn.href = driverUrl;

  if (whatsappBtn) {
    const msg = `Hello Driver, please click this link on your smartphone to start live GPS tracking for truck ${reg || 'your vehicle'}:\n${driverUrl}`;
    whatsappBtn.href = `https://api.whatsapp.com/send?text=${encodeURIComponent(msg)}`;
  }

  // Generate QR Code on canvas
  if (canvas && typeof QRCode !== 'undefined') {
    QRCode.toCanvas(canvas, driverUrl, {
      width: 170,
      margin: 1,
      color: {
        dark: '#0f172a',
        light: '#ffffff'
      }
    }, function (error) {
      if (error) console.error('QR code render error:', error);
    });
  }
}

function openMobileModalForTruck(regNumber) {
  const truckSelect = document.getElementById('modal-phone-truck-select');
  if (truckSelect) {
    truckSelect.value = regNumber;
    updateMobileTrackLink();
  }
  const modalEl = document.getElementById('mobileTrackModal');
  if (modalEl) {
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    modal.show();
  }
}
