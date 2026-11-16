/**
 * Vehicle Fleet Roster, Registration, and Specs Management.
 */
let allDriversList = [];
let vehiclePollTimer = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  await loadDriversForSelect();
  await loadVehicles();

  // Auto-check vehicle and hardware online/offline status every 10 seconds
  if (!vehiclePollTimer) {
    vehiclePollTimer = setInterval(() => {
      const openModal = document.querySelector('.modal.show');
      if (!openModal) {
        loadVehicles(true);
      }
    }, 10000);
  }

  const addForm = document.getElementById('add-vehicle-form');
  if (addForm) {
    addForm.addEventListener('submit', handleAddVehicle);
  }

  const editForm = document.getElementById('edit-vehicle-form');
  if (editForm) {
    editForm.addEventListener('submit', handleEditVehicle);
  }

  const searchInput = document.getElementById('vehicle-search');
  if (searchInput) {
    searchInput.addEventListener('input', debounce(() => loadVehicles(), 300));
  }

  const statusFilter = document.getElementById('vehicle-status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', () => loadVehicles());
  }
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

async function loadDriversForSelect() {
  try {
    const res = await ApiClient.get('/drivers?limit=100');
    if (res.success && Array.isArray(res.data)) {
      allDriversList = res.data;
      populateDriverDropdowns();
    }
  } catch (err) {
    console.warn('Could not pre-load drivers:', err);
  }
}

function populateDriverDropdowns() {
  const addSelect = document.getElementById('veh-driver');
  const editSelect = document.getElementById('edit-veh-driver');

  const options = [
    '<option value="">-- No Driver Assigned --</option>',
    ...allDriversList.map(d => `<option value="${d.id}">${d.name} (${d.license_number})</option>`)
  ].join('');

  if (addSelect) addSelect.innerHTML = options;
  if (editSelect) editSelect.innerHTML = options;
}

async function loadVehicles(silent = false) {
  const tableBody = document.getElementById('vehicles-table-body');
  if (!tableBody) return;

  const search = document.getElementById('vehicle-search')?.value.trim() || '';
  const status = document.getElementById('vehicle-status-filter')?.value || '';

  if (!silent) {
    Utils.renderLoading(tableBody, 'Loading fleet inventory & hardware status...');
  }

  try {
    let endpoint = '/vehicles?limit=50&include_telemetry=true';
    if (search) endpoint += `&search=${encodeURIComponent(search)}`;
    if (status) endpoint += `&status=${encodeURIComponent(status)}`;

    const res = await ApiClient.get(endpoint);
    if (res.success && Array.isArray(res.data)) {
      if (res.data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-5"><i class="bi bi-truck display-6 d-block mb-2 opacity-50"></i>No vehicles matching query</td></tr>';
        return;
      }

      tableBody.innerHTML = res.data.map(v => {
        const isOnline = Boolean(v.is_online);
        const driverName = v.assigned_driver ? v.assigned_driver.name : '<span class="text-muted">Unassigned</span>';
        const lastSpeed = v.last_known_telemetry ? Utils.formatSpeed(v.last_known_telemetry.speed_kmh) : '0.0 km/h';
        const pingTime = v.last_updated ? Utils.formatDate(v.last_updated) : (v.last_known_telemetry?.recorded_at ? Utils.formatDate(v.last_known_telemetry.recorded_at) : 'No signal');

        // Hardware GPS device status check
        let hardwareHtml = '';
        if (v.gps_device && v.gps_device.imei) {
          const hwOnline = Boolean(v.gps_device.is_online);
          hardwareHtml = `
            <div class="d-flex flex-column gap-1">
              <span class="d-inline-flex align-items-center gap-1 font-monospace small">
                <i class="bi bi-cpu text-muted"></i><code>${v.gps_device.imei}</code>
              </span>
              <span>
                ${hwOnline 
                  ? '<span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25" style="font-size: 0.65rem;"><i class="bi bi-broadcast me-1"></i>Hardware Online</span>'
                  : '<span class="badge bg-secondary bg-opacity-10 text-secondary border border-secondary border-opacity-25" style="font-size: 0.65rem;"><i class="bi bi-slash-circle me-1"></i>Hardware Offline</span>'
                }
              </span>
            </div>
          `;
        } else if (isOnline) {
          hardwareHtml = `
            <div class="d-flex flex-column gap-1">
              <span class="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25" style="font-size: 0.7rem; width: fit-content;">
                <i class="bi bi-phone me-1"></i>Driver Phone GPS
              </span>
              <span class="badge bg-success bg-opacity-10 text-success border border-success border-opacity-25" style="font-size: 0.65rem; width: fit-content;">
                <i class="bi bi-broadcast me-1"></i>Mobile Online
              </span>
            </div>
          `;
        } else {
          hardwareHtml = `
            <span class="badge bg-secondary bg-opacity-25 text-dim border border-secondary border-opacity-25" style="font-size: 0.7rem;">
              <i class="bi bi-dash-circle me-1"></i>No Hardware Tracker
            </span>
          `;
        }

        return `
          <tr>
            <td class="fw-bold text-white">
              <i class="bi bi-truck text-primary me-2"></i>${v.registration_number}
            </td>
            <td>${v.make} ${v.model} ${v.year ? `(${v.year})` : ''}</td>
            <td>${driverName}</td>
            <td>${Utils.getStatusBadge(v.status, isOnline)}</td>
            <td>${hardwareHtml}</td>
            <td>${lastSpeed}</td>
            <td>${Utils.formatDistance(v.current_odometer_km)}</td>
            <td>
              <span class="${isOnline ? 'text-success' : 'text-muted'}" style="font-size: 0.8rem;" title="Last telemetry ping">
                <i class="bi ${isOnline ? 'bi-broadcast text-success' : 'bi-clock-history'} me-1"></i>${pingTime}
              </span>
            </td>
            <td>
              <div class="btn-group btn-group-sm">
                <a href="/live-tracking.html?focus=${v.id}" class="btn btn-outline-info" title="Live Track">
                  <i class="bi bi-geo-alt"></i>
                </a>
                <button class="btn btn-outline-primary" data-min-role="fleet_manager" onclick='openEditModal(${JSON.stringify(v)})' title="Edit Vehicle">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-outline-danger" data-min-role="fleet_manager" onclick="deleteVehicle('${v.id}')" title="Delete">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');

      Auth.initUI();
    }
  } catch (err) {
    console.error('Error loading vehicles:', err);
    if (!silent) {
      Utils.renderError(tableBody, 'Failed to fetch vehicles from API', () => loadVehicles());
    }
  }
}

async function handleAddVehicle(e) {
  e.preventDefault();
  const form = e.target;
  const regNumber = document.getElementById('veh-reg').value.trim().toUpperCase();
  const make = document.getElementById('veh-make').value.trim();
  const model = document.getElementById('veh-model').value.trim();
  const year = document.getElementById('veh-year').value;
  const color = document.getElementById('veh-color').value.trim();
  const fuelType = document.getElementById('veh-fuel-type').value;
  const fuelCapacity = document.getElementById('veh-fuel-capacity').value;
  const speedLimit = document.getElementById('veh-speed-limit').value;
  const driverId = document.getElementById('veh-driver').value;
  const imei = document.getElementById('veh-imei').value.trim();
  const notes = document.getElementById('veh-notes').value.trim();

  try {
    const payload = {
      registration_number: regNumber,
      make,
      model,
      year: year ? parseInt(year) : null,
      color: color || null,
      fuel_type: fuelType,
      fuel_capacity_litres: fuelCapacity ? parseFloat(fuelCapacity) : 300,
      speed_limit_kmh: speedLimit ? parseFloat(speedLimit) : 80,
      assigned_driver_id: driverId || null,
      device_imei: imei || null,
      notes: notes || null,
    };

    const res = await ApiClient.post('/vehicles', payload);
    if (res.success) {
      Utils.showToast(`Vehicle ${regNumber} registered successfully!`, 'success');
      const modalEl = document.getElementById('addVehicleModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      form.reset();
      loadVehicles();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to add vehicle', 'danger');
  }
}

function openEditModal(v) {
  document.getElementById('edit-veh-id').value = v.id;
  document.getElementById('edit-veh-reg').value = v.registration_number;
  document.getElementById('edit-veh-make').value = v.make;
  document.getElementById('edit-veh-model').value = v.model;
  document.getElementById('edit-veh-year').value = v.year || '';
  document.getElementById('edit-veh-color').value = v.color || '';
  document.getElementById('edit-veh-status').value = v.status || 'active';
  document.getElementById('edit-veh-fuel-type').value = v.fuel_type || 'diesel';
  document.getElementById('edit-veh-speed-limit').value = v.speed_limit_kmh || 80;
  document.getElementById('edit-veh-driver').value = v.assigned_driver_id || '';
  document.getElementById('edit-veh-notes').value = v.notes || '';

  const modal = new bootstrap.Modal(document.getElementById('editVehicleModal'));
  modal.show();
}

async function handleEditVehicle(e) {
  e.preventDefault();
  const id = document.getElementById('edit-veh-id').value;
  const make = document.getElementById('edit-veh-make').value.trim();
  const model = document.getElementById('edit-veh-model').value.trim();
  const year = document.getElementById('edit-veh-year').value;
  const color = document.getElementById('edit-veh-color').value.trim();
  const status = document.getElementById('edit-veh-status').value;
  const fuelType = document.getElementById('edit-veh-fuel-type').value;
  const speedLimit = document.getElementById('edit-veh-speed-limit').value;
  const driverId = document.getElementById('edit-veh-driver').value;
  const notes = document.getElementById('edit-veh-notes').value.trim();

  try {
    const payload = {
      make,
      model,
      year: year ? parseInt(year) : null,
      color: color || null,
      status,
      fuel_type: fuelType,
      speed_limit_kmh: speedLimit ? parseFloat(speedLimit) : 80,
      assigned_driver_id: driverId || null,
      notes: notes || null,
    };

    const res = await ApiClient.put(`/vehicles/${id}`, payload);
    if (res.success) {
      Utils.showToast('Vehicle updated successfully!', 'success');
      const modalEl = document.getElementById('editVehicleModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      loadVehicles();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to update vehicle', 'danger');
  }
}

async function deleteVehicle(id) {
  if (confirm('Are you sure you want to remove this vehicle from your fleet?')) {
    try {
      await ApiClient.delete(`/vehicles/${id}`);
      Utils.showToast('Vehicle removed from fleet', 'success');
      loadVehicles();
    } catch (err) {
      Utils.showToast(err.message || 'Failed to delete vehicle', 'danger');
    }
  }
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}
