/**
 * Geofence Management, Boundary Visualization, and Point-in-Polygon Testing.
 */
let fenceMap = null;
let allGeofences = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  fenceMap = new FleetMap('geofence-map');

  // Allow clicking on map to fill coordinate inputs
  if (fenceMap && fenceMap.map) {
    fenceMap.map.on('click', (e) => {
      const latInput = document.getElementById('fence-lat');
      const lngInput = document.getElementById('fence-lng');
      if (latInput && lngInput) {
        latInput.value = e.latlng.lat.toFixed(5);
        lngInput.value = e.latlng.lng.toFixed(5);
        Utils.showToast(`Coordinates set to (${latInput.value}, ${lngInput.value})`, 'info');
      }
    });
  }

  await loadGeofences();

  const form = document.getElementById('add-geofence-form');
  if (form) {
    form.addEventListener('submit', handleAddGeofence);
  }

  const checkForm = document.getElementById('check-point-form');
  if (checkForm) {
    checkForm.addEventListener('submit', handleCheckPoint);
  }

  const radiusRange = document.getElementById('fence-radius');
  const radiusDisplay = document.getElementById('fence-radius-display');
  if (radiusRange && radiusDisplay) {
    radiusRange.addEventListener('input', () => {
      radiusDisplay.textContent = `${radiusRange.value}m`;
    });
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

async function loadGeofences() {
  const listEl = document.getElementById('geofence-list');
  const fenceSelect = document.getElementById('test-fence-select');

  try {
    const res = await ApiClient.get('/geofences?limit=50');
    if (res.success && Array.isArray(res.data)) {
      allGeofences = res.data;

      if (fenceMap) fenceMap.renderGeofences(allGeofences);

      if (fenceSelect) {
        fenceSelect.innerHTML = [
          '<option value="">-- Choose Geofence Zone --</option>',
          ...allGeofences.map(f => `<option value="${f.id}">${f.name} (${f.fence_type})</option>`)
        ].join('');
      }

      if (listEl) {
        if (allGeofences.length === 0) {
          listEl.innerHTML = '<div class="text-center text-muted p-4"><i class="bi bi-bounding-box display-6 d-block mb-2 opacity-50"></i>No geofences created yet.</div>';
          return;
        }

        listEl.innerHTML = allGeofences.map(f => `
          <div class="p-3 border-bottom border-secondary border-opacity-10 cursor-pointer"
               onclick="focusGeofence('${f.id}')"
               style="cursor: pointer; transition: background 0.2s;"
               onmouseover="this.style.background='rgba(255,255,255,0.03)'"
               onmouseout="this.style.background='transparent'">
            <div class="d-flex justify-content-between align-items-center mb-1">
              <span class="fw-bold" style="color: ${f.color_hex || '#3B82F6'};">
                <i class="bi bi-geo-alt-fill me-1"></i>${f.name}
              </span>
              <span class="badge bg-secondary text-uppercase">${f.fence_type}</span>
            </div>
            <div class="small text-muted mb-2">
              ${f.fence_type === 'circle' ? `Radius: ${f.radius_meters || 1000}m &bull; Center: ${Number(f.center_latitude || 0).toFixed(4)}, ${Number(f.center_longitude || 0).toFixed(4)}` : 'Polygon Area'}
            </div>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-outline-danger flex-grow-1" data-min-role="fleet_manager" onclick="event.stopPropagation(); deleteGeofence('${f.id}')">
                <i class="bi bi-trash me-1"></i>Delete
              </button>
            </div>
          </div>
        `).join('');

        Auth.initUI();
      }
    }
  } catch (err) {
    console.error('Error loading geofences:', err);
  }
}

function focusGeofence(id) {
  const target = allGeofences.find(f => f.id === id);
  if (target && fenceMap && fenceMap.map) {
    if (target.center_latitude && target.center_longitude) {
      fenceMap.map.flyTo([target.center_latitude, target.center_longitude], 14);
    }
  }
}

async function handleAddGeofence(e) {
  e.preventDefault();
  const form = e.target;
  const name = document.getElementById('fence-name').value.trim();
  const lat = parseFloat(document.getElementById('fence-lat').value);
  const lng = parseFloat(document.getElementById('fence-lng').value);
  const radius = parseFloat(document.getElementById('fence-radius').value || '1000');
  const color = document.getElementById('fence-color').value || '#3B82F6';
  const description = document.getElementById('fence-desc').value.trim();

  try {
    const payload = {
      name,
      fence_type: 'circle',
      center_latitude: lat,
      center_longitude: lng,
      radius_meters: radius,
      color_hex: color,
      description: description || null,
      is_active: true,
    };

    const res = await ApiClient.post('/geofences', payload);
    if (res.success) {
      Utils.showToast(`Geofence "${name}" deployed!`, 'success');
      form.reset();
      const modalEl = document.getElementById('addGeofenceModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      loadGeofences();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to create geofence', 'danger');
  }
}

async function handleCheckPoint(e) {
  e.preventDefault();
  const fenceId = document.getElementById('test-fence-select').value;
  const lat = parseFloat(document.getElementById('test-lat').value);
  const lng = parseFloat(document.getElementById('test-lng').value);
  const resultAlert = document.getElementById('test-result-alert');

  if (!fenceId) {
    Utils.showToast('Select a geofence to test against', 'warning');
    return;
  }

  try {
    const res = await ApiClient.post(`/geofences/${fenceId}/check-point`, {
      latitude: lat,
      longitude: lng,
    });

    if (res.success && res.data) {
      const isInside = res.data.is_inside;
      resultAlert.className = `alert alert-${isInside ? 'success' : 'danger'} mt-3 show`;
      resultAlert.innerHTML = `
        <i class="bi bi-${isInside ? 'check-circle-fill' : 'x-circle-fill'} me-2"></i>
        Point (${lat}, ${lng}) is <strong>${isInside ? 'INSIDE' : 'OUTSIDE'}</strong> the geofence perimeter.
        ${res.data.distance_meters !== undefined ? `<br><small>Distance to center: ${Number(res.data.distance_meters).toFixed(1)}m</small>` : ''}
      `;
    }
  } catch (err) {
    resultAlert.className = 'alert alert-danger mt-3 show';
    resultAlert.textContent = err.message || 'Check failed';
  }
}

async function deleteGeofence(id) {
  if (confirm('Delete this geofence boundary zone?')) {
    try {
      await ApiClient.delete(`/geofences/${id}`);
      Utils.showToast('Geofence zone deleted', 'success');
      window.location.reload();
    } catch (err) {
      Utils.showToast(err.message || 'Failed to delete geofence', 'danger');
    }
  }
}
