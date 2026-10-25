/**
 * Trip Management, Cargo Status (Loaded/Empty), Start/Complete/Cancel,
 * Stop Durations, and Incident Events.
 */
let allVehiclesList = [];
let allDriversList = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  await loadSelectOptions();
  await loadTrips();

  const startTripForm = document.getElementById('start-trip-form');
  if (startTripForm) {
    startTripForm.addEventListener('submit', handleStartTrip);
  }

  const completeTripForm = document.getElementById('complete-trip-form');
  if (completeTripForm) {
    completeTripForm.addEventListener('submit', handleCompleteTrip);
  }

  const cancelTripForm = document.getElementById('cancel-trip-form');
  if (cancelTripForm) {
    cancelTripForm.addEventListener('submit', handleCancelTrip);
  }

  const statusFilter = document.getElementById('trip-status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', () => loadTrips());
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

async function loadSelectOptions() {
  try {
    const [vehRes, drvRes] = await Promise.all([
      ApiClient.get('/vehicles?limit=100'),
      ApiClient.get('/drivers?limit=100'),
    ]);

    if (vehRes.success && Array.isArray(vehRes.data)) {
      allVehiclesList = vehRes.data;
      const vehSelect = document.getElementById('start-trip-vehicle');
      if (vehSelect) {
        vehSelect.innerHTML = [
          '<option value="">-- Choose Truck --</option>',
          ...allVehiclesList.map(v => `<option value="${v.id}">${v.registration_number} (${v.make} ${v.model})</option>`)
        ].join('');
      }
    }

    if (drvRes.success && Array.isArray(drvRes.data)) {
      allDriversList = drvRes.data;
      const drvSelect = document.getElementById('start-trip-driver');
      if (drvSelect) {
        drvSelect.innerHTML = [
          '<option value="">-- Choose Driver (optional) --</option>',
          ...allDriversList.map(d => `<option value="${d.id}">${d.name} (${d.license_number})</option>`)
        ].join('');
      }
    }
  } catch (err) {
    console.warn('Could not pre-load vehicle or driver lists:', err);
  }
}

async function loadTrips() {
  const tableBody = document.getElementById('trips-table-body');
  if (!tableBody) return;

  const status = document.getElementById('trip-status-filter')?.value || '';
  Utils.renderLoading(tableBody, 'Fetching trip manifests...');

  try {
    let endpoint = '/trips?limit=50';
    if (status) endpoint += `&status=${encodeURIComponent(status)}`;

    const res = await ApiClient.get(endpoint);
    if (res.success && Array.isArray(res.data)) {
      if (res.data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-5"><i class="bi bi-map display-6 d-block mb-2 opacity-50"></i>No trips recorded.</td></tr>';
        return;
      }

      tableBody.innerHTML = res.data.map(t => {
        const isInProgress = t.status === 'in_progress';
        const isLoaded = (t.load_status || 'empty') === 'loaded';
        const toggleLoadBtn = isInProgress ? `
          <button class="btn btn-sm btn-outline-light me-1" title="Toggle Loaded/Empty" onclick="toggleLoadStatus('${t.id}', '${isLoaded ? 'empty' : 'loaded'}')">
            <i class="bi bi-arrow-repeat"></i>
          </button>
        ` : '';

        const actionBtns = isInProgress ? `
          <div class="btn-group btn-group-sm">
            ${toggleLoadBtn}
            <button class="btn btn-outline-success" onclick="openCompleteTripModal('${t.id}')" title="Complete Journey">
              <i class="bi bi-check-circle"></i>
            </button>
            <button class="btn btn-outline-danger" onclick="openCancelTripModal('${t.id}')" title="Cancel Trip">
              <i class="bi bi-x-circle"></i>
            </button>
          </div>
        ` : `
          <a href="/playback.html?trip_id=${t.id}" class="btn btn-sm btn-outline-primary" title="Scrub & Replay Route">
            <i class="bi bi-play-circle me-1"></i>Playback
          </a>
        `;

        return `
          <tr>
            <td class="fw-bold text-white">
              <i class="bi bi-truck me-2 text-primary"></i>${t.registration_number || 'Vehicle'}
            </td>
            <td>${t.driver_name || '<span class="text-muted">Unassigned</span>'}</td>
            <td>
              <div class="d-flex align-items-center gap-1">
                ${Utils.getLoadStatusBadge(t.load_status)}
              </div>
            </td>
            <td>${Utils.getStatusBadge(t.status)}</td>
            <td>
              <div class="small fw-semibold text-white">${Utils.formatDate(t.start_time)}</div>
              <div class="small text-muted">${t.end_time ? Utils.formatDate(t.end_time) : '<span class="text-success">Active En Route</span>'}</div>
            </td>
            <td>${Utils.formatDistance(t.distance_km)}</td>
            <td>${Utils.formatDuration(t.duration_minutes)}</td>
            <td>${Utils.formatSpeed(t.avg_speed_kmh)}</td>
            <td>
              <div class="d-flex align-items-center gap-1">
                <button class="btn btn-sm btn-outline-info" onclick="viewTripDetails('${t.id}')" title="View Stops & Events">
                  <i class="bi bi-eye"></i>
                </button>
                ${actionBtns}
              </div>
            </td>
          </tr>
        `;
      }).join('');

      Auth.initUI();
    }
  } catch (err) {
    console.error('Error loading trips:', err);
    Utils.renderError(tableBody, 'Failed to fetch trip logs', () => loadTrips());
  }
}

async function handleStartTrip(e) {
  e.preventDefault();
  const form = e.target;
  const vehicleId = document.getElementById('start-trip-vehicle').value;
  const driverId = document.getElementById('start-trip-driver').value;
  const startLat = parseFloat(document.getElementById('start-trip-lat').value);
  const startLng = parseFloat(document.getElementById('start-trip-lng').value);
  const loadStatus = document.getElementById('start-trip-load-status').value;
  const notes = document.getElementById('start-trip-notes').value.trim();

  try {
    const payload = {
      vehicle_id: vehicleId,
      driver_id: driverId || null,
      start_latitude: startLat,
      start_longitude: startLng,
      load_status: loadStatus,
      notes: notes || null,
    };

    const res = await ApiClient.post('/trips', payload);
    if (res.success) {
      Utils.showToast('Trip journey initiated successfully!', 'success');
      const modalEl = document.getElementById('startTripModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      form.reset();
      loadTrips();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to start trip', 'danger');
  }
}

function openCompleteTripModal(tripId) {
  document.getElementById('complete-trip-id').value = tripId;
  const modal = new bootstrap.Modal(document.getElementById('completeTripModal'));
  modal.show();
}

async function handleCompleteTrip(e) {
  e.preventDefault();
  const tripId = document.getElementById('complete-trip-id').value;
  const endLat = parseFloat(document.getElementById('complete-trip-lat').value);
  const endLng = parseFloat(document.getElementById('complete-trip-lng').value);
  const notes = document.getElementById('complete-trip-notes').value.trim();

  try {
    const res = await ApiClient.post(`/trips/${tripId}/complete`, {
      end_latitude: endLat,
      end_longitude: endLng,
      notes: notes || null,
    });
    if (res.success) {
      Utils.showToast('Trip completed successfully!', 'success');
      const modalEl = document.getElementById('completeTripModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      loadTrips();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to complete trip', 'danger');
  }
}

function openCancelTripModal(tripId) {
  document.getElementById('cancel-trip-id').value = tripId;
  const modal = new bootstrap.Modal(document.getElementById('cancelTripModal'));
  modal.show();
}

async function handleCancelTrip(e) {
  e.preventDefault();
  const tripId = document.getElementById('cancel-trip-id').value;
  const reason = document.getElementById('cancel-trip-reason').value.trim();

  try {
    const res = await ApiClient.post(`/trips/${tripId}/cancel`, {
      reason: reason || 'Cancelled by dispatcher',
    });
    if (res.success) {
      Utils.showToast('Trip cancelled', 'warning');
      const modalEl = document.getElementById('cancelTripModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      loadTrips();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to cancel trip', 'danger');
  }
}

async function toggleLoadStatus(tripId, newStatus) {
  try {
    const res = await ApiClient.put(`/trips/${tripId}/load-status`, {
      load_status: newStatus
    });
    if (res.success) {
      Utils.showToast(`Cargo status updated to ${newStatus.toUpperCase()}`, 'success');
      loadTrips();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to update load status', 'danger');
  }
}

async function viewTripDetails(tripId) {
  const modalEl = document.getElementById('tripDetailsModal');
  const modal = new bootstrap.Modal(modalEl);
  modal.show();

  const titleEl = document.getElementById('trip-details-title');
  const stopsTbody = document.getElementById('trip-stops-tbody');
  const eventsTbody = document.getElementById('trip-events-tbody');
  const statsContainer = document.getElementById('trip-stats-container');
  const detectStopsBtn = document.getElementById('btn-detect-stops');

  if (stopsTbody) stopsTbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted"><div class="spinner-border spinner-border-sm me-2"></div>Loading stops...</td></tr>';
  if (eventsTbody) eventsTbody.innerHTML = '<tr><td colspan="4" class="text-center py-3 text-muted"><div class="spinner-border spinner-border-sm me-2"></div>Loading events...</td></tr>';

  try {
    const [tripRes, stopsRes, eventsRes] = await Promise.all([
      ApiClient.get(`/trips/${tripId}`),
      ApiClient.get(`/trips/${tripId}/stops`),
      ApiClient.get(`/trips/${tripId}/events`),
    ]);

    if (tripRes.success && tripRes.data) {
      const t = tripRes.data;
      if (titleEl) titleEl.textContent = `Trip: ${t.registration_number || 'Vehicle'} (${Utils.formatDate(t.start_time)})`;

      if (statsContainer) {
        statsContainer.innerHTML = `
          <div class="row g-2 mb-3">
            <div class="col-sm-3 col-6">
              <div class="p-2 border border-secondary border-opacity-25 rounded bg-dark">
                <small class="text-muted d-block">Distance</small>
                <span class="fw-bold">${Utils.formatDistance(t.distance_km)}</span>
              </div>
            </div>
            <div class="col-sm-3 col-6">
              <div class="p-2 border border-secondary border-opacity-25 rounded bg-dark">
                <small class="text-muted d-block">Duration</small>
                <span class="fw-bold">${Utils.formatDuration(t.duration_minutes)}</span>
              </div>
            </div>
            <div class="col-sm-3 col-6">
              <div class="p-2 border border-secondary border-opacity-25 rounded bg-dark">
                <small class="text-muted d-block">Max Speed</small>
                <span class="fw-bold">${Utils.formatSpeed(t.max_speed_kmh)}</span>
              </div>
            </div>
            <div class="col-sm-3 col-6">
              <div class="p-2 border border-secondary border-opacity-25 rounded bg-dark">
                <small class="text-muted d-block">Cargo Status</small>
                <span class="fw-bold">${Utils.getLoadStatusBadge(t.load_status)}</span>
              </div>
            </div>
          </div>
        `;
      }

      if (detectStopsBtn) {
        detectStopsBtn.onclick = async () => {
          detectStopsBtn.disabled = true;
          detectStopsBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Detecting...';
          try {
            await ApiClient.post(`/trips/${tripId}/detect-stops`, {});
            Utils.showToast('Stop detection algorithm finished!', 'success');
            viewTripDetails(tripId);
          } catch (e) {
            Utils.showToast(e.message || 'Detection failed', 'danger');
          } finally {
            detectStopsBtn.disabled = false;
            detectStopsBtn.innerHTML = '<i class="bi bi-magic me-1"></i>Detect Stops';
          }
        };
      }
    }

    // Render stops
    if (stopsRes.success && Array.isArray(stopsRes.data)) {
      if (stopsRes.data.length === 0) {
        stopsTbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">No stops detected yet for this trip.</td></tr>';
      } else {
        stopsTbody.innerHTML = stopsRes.data.map((s, idx) => `
          <tr>
            <td class="fw-bold">#${idx + 1}</td>
            <td><code>${Number(s.latitude).toFixed(4)}, ${Number(s.longitude).toFixed(4)}</code></td>
            <td>${Utils.formatDuration(s.duration_minutes)}</td>
            <td><small class="text-muted">${Utils.formatDate(s.arrived_at)} &rarr; ${s.departed_at ? Utils.formatDate(s.departed_at) : 'Still Stopped'}</small></td>
          </tr>
        `).join('');
      }
    }

    // Render events
    if (eventsRes.success && Array.isArray(eventsRes.data)) {
      if (eventsRes.data.length === 0) {
        eventsTbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-3">No incident events recorded.</td></tr>';
      } else {
        eventsTbody.innerHTML = eventsRes.data.map(e => `
          <tr>
            <td><span class="badge bg-secondary">${e.event_type}</span></td>
            <td>${e.description || '-'}</td>
            <td>${e.speed_kmh ? Utils.formatSpeed(e.speed_kmh) : '-'}</td>
            <td><small class="text-muted">${Utils.formatDate(e.occurred_at)}</small></td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Error fetching trip details:', err);
    Utils.showToast(err.message || 'Failed to load trip details', 'danger');
  }
}
