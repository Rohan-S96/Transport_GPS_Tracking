/**
 * Driver Roster, Safety Scores, and Assignment Manager.
 */
document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  await loadDrivers();

  const addForm = document.getElementById('add-driver-form');
  if (addForm) {
    addForm.addEventListener('submit', handleAddDriver);
  }

  const editForm = document.getElementById('edit-driver-form');
  if (editForm) {
    editForm.addEventListener('submit', handleEditDriver);
  }

  const searchInput = document.getElementById('driver-search');
  if (searchInput) {
    searchInput.addEventListener('input', debounce(() => loadDrivers(), 300));
  }

  const statusFilter = document.getElementById('driver-status-filter');
  if (statusFilter) {
    statusFilter.addEventListener('change', () => loadDrivers());
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

async function loadDrivers() {
  const container = document.getElementById('drivers-grid');
  if (!container) return;

  const search = document.getElementById('driver-search')?.value.trim() || '';
  const status = document.getElementById('driver-status-filter')?.value || '';

  Utils.renderLoading(container, 'Loading drivers roster...');

  try {
    let endpoint = '/drivers?limit=50';
    if (search) endpoint += `&search=${encodeURIComponent(search)}`;
    if (status) endpoint += `&status=${encodeURIComponent(status)}`;

    const res = await ApiClient.get(endpoint);
    if (res.success && Array.isArray(res.data)) {
      if (res.data.length === 0) {
        container.innerHTML = '<div class="col-12 text-center text-muted py-5"><i class="bi bi-person-x display-6 d-block mb-2 opacity-50"></i>No drivers found.</div>';
        return;
      }

      container.innerHTML = res.data.map(d => {
        const score = d.safety_score !== undefined ? d.safety_score : 100;
        const scoreColor = score >= 85 ? 'text-success' : score >= 70 ? 'text-warning' : 'text-danger';
        const assignedTruck = d.assigned_vehicle_reg ? `<span class="badge bg-primary bg-opacity-25 text-info"><i class="bi bi-truck me-1"></i>${d.assigned_vehicle_reg}</span>` : '<span class="text-muted">Unassigned</span>';

        return `
          <div class="col-md-6 col-lg-4 mb-4">
            <div class="kpi-card h-100 position-relative">
              <div class="d-flex align-items-center justify-content-between mb-3">
                <div class="d-flex align-items-center gap-3">
                  <div class="kpi-icon-wrap kpi-icon-blue fs-4">
                    <i class="bi bi-person-badge-fill"></i>
                  </div>
                  <div>
                    <h5 class="mb-0 text-white fw-bold">${d.first_name} ${d.last_name}</h5>
                    <small class="text-muted">Lic: <code>${d.license_number}</code></small>
                  </div>
                </div>
                <div>
                  ${Utils.getStatusBadge(d.status)}
                </div>
              </div>

              <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary border-opacity-10 small">
                <span class="text-muted">Phone Number</span>
                <span class="text-white">${d.phone_number || 'N/A'}</span>
              </div>

              <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary border-opacity-10 small">
                <span class="text-muted">Safety Score</span>
                <span class="fw-bold ${scoreColor}"><i class="bi bi-shield-check me-1"></i>${score}%</span>
              </div>

              <div class="d-flex justify-content-between align-items-center mb-2 pb-2 border-bottom border-secondary border-opacity-10 small">
                <span class="text-muted">Assigned Truck</span>
                <span>${assignedTruck}</span>
              </div>

              <div class="d-flex justify-content-between align-items-center mb-3 small">
                <span class="text-muted">License Expiry</span>
                <span>${d.license_expiry ? Utils.formatDate(d.license_expiry).split(',')[0] : 'N/A'}</span>
              </div>

              <div class="d-flex gap-2 pt-2 border-top border-secondary border-opacity-10">
                <button class="btn btn-sm btn-outline-primary flex-grow-1" data-min-role="fleet_manager" onclick='openEditDriverModal(${JSON.stringify(d)})'>
                  <i class="bi bi-pencil me-1"></i>Edit
                </button>
                <button class="btn btn-sm btn-outline-danger" data-min-role="fleet_manager" onclick="deleteDriver('${d.id}')">
                  <i class="bi bi-trash"></i>
                </button>
              </div>
            </div>
          </div>
        `;
      }).join('');

      Auth.initUI();
    }
  } catch (err) {
    console.error('Error loading drivers:', err);
    Utils.renderError(container, 'Failed to fetch driver records', () => loadDrivers());
  }
}

async function handleAddDriver(e) {
  e.preventDefault();
  const form = e.target;
  const firstName = document.getElementById('driver-first-name').value.trim();
  const lastName = document.getElementById('driver-last-name').value.trim();
  const licenseNumber = document.getElementById('driver-license').value.trim();
  const licenseExpiry = document.getElementById('driver-expiry').value;
  const phone = document.getElementById('driver-phone').value.trim();
  const email = document.getElementById('driver-email').value.trim();
  const experienceYears = document.getElementById('driver-exp').value;

  try {
    const payload = {
      first_name: firstName,
      last_name: lastName,
      license_number: licenseNumber,
      license_expiry: licenseExpiry || null,
      phone_number: phone || null,
      email: email || null,
      experience_years: experienceYears ? parseInt(experienceYears) : null,
    };

    const res = await ApiClient.post('/drivers', payload);
    if (res.success) {
      Utils.showToast(`Driver ${firstName} ${lastName} added successfully!`, 'success');
      const modalEl = document.getElementById('addDriverModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      form.reset();
      loadDrivers();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to add driver', 'danger');
  }
}

function openEditDriverModal(d) {
  document.getElementById('edit-driver-id').value = d.id;
  document.getElementById('edit-driver-first-name').value = d.first_name || '';
  document.getElementById('edit-driver-last-name').value = d.last_name || '';
  document.getElementById('edit-driver-license').value = d.license_number || '';
  document.getElementById('edit-driver-phone').value = d.phone_number || '';
  document.getElementById('edit-driver-email').value = d.email || '';
  document.getElementById('edit-driver-status').value = d.status || 'active';
  document.getElementById('edit-driver-score').value = d.safety_score !== undefined ? d.safety_score : 100;

  const modal = new bootstrap.Modal(document.getElementById('editDriverModal'));
  modal.show();
}

async function handleEditDriver(e) {
  e.preventDefault();
  const id = document.getElementById('edit-driver-id').value;
  const firstName = document.getElementById('edit-driver-first-name').value.trim();
  const lastName = document.getElementById('edit-driver-last-name').value.trim();
  const licenseNumber = document.getElementById('edit-driver-license').value.trim();
  const phone = document.getElementById('edit-driver-phone').value.trim();
  const email = document.getElementById('edit-driver-email').value.trim();
  const status = document.getElementById('edit-driver-status').value;
  const safetyScore = document.getElementById('edit-driver-score').value;

  try {
    const payload = {
      first_name: firstName,
      last_name: lastName,
      license_number: licenseNumber,
      phone_number: phone || null,
      email: email || null,
      status: status,
      safety_score: safetyScore ? parseFloat(safetyScore) : 100,
    };

    const res = await ApiClient.put(`/drivers/${id}`, payload);
    if (res.success) {
      Utils.showToast('Driver updated successfully!', 'success');
      const modalEl = document.getElementById('editDriverModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      loadDrivers();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to update driver', 'danger');
  }
}

async function deleteDriver(id) {
  if (confirm('Are you sure you want to remove this driver?')) {
    try {
      await ApiClient.delete(`/drivers/${id}`);
      Utils.showToast('Driver removed successfully', 'success');
      loadDrivers();
    } catch (err) {
      Utils.showToast(err.message || 'Failed to delete driver', 'danger');
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
