/**
 * Freight Customer & Transport Client Company Management.
 */
let currentManagingCompanyId = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  await loadCompanies();

  const addForm = document.getElementById('add-company-form');
  if (addForm) {
    addForm.addEventListener('submit', handleAddCompany);
  }

  const editForm = document.getElementById('edit-company-form');
  if (editForm) {
    editForm.addEventListener('submit', handleEditCompany);
  }

  const addLocForm = document.getElementById('add-location-form');
  if (addLocForm) {
    addLocForm.addEventListener('submit', handleAddLocation);
  }

  const searchInput = document.getElementById('company-search');
  if (searchInput) {
    searchInput.addEventListener('input', debounce(() => loadCompanies(), 300));
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

async function loadCompanies() {
  const tableBody = document.getElementById('companies-table-body');
  if (!tableBody) return;

  const search = document.getElementById('company-search')?.value.trim() || '';
  Utils.renderLoading(tableBody, 'Loading transport clients...');

  try {
    let endpoint = '/companies?limit=50';
    if (search) endpoint += `&search=${encodeURIComponent(search)}`;

    const res = await ApiClient.get(endpoint);
    if (res.success && Array.isArray(res.data)) {
      if (res.data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-5"><i class="bi bi-buildings display-6 d-block mb-2 opacity-50"></i>No companies registered yet.</td></tr>';
        return;
      }

      tableBody.innerHTML = res.data.map(c => {
        const locCount = c.locations ? c.locations.length : 0;
        return `
          <tr>
            <td class="fw-bold text-white">
              <i class="bi bi-building text-primary me-2"></i>${c.name}
            </td>
            <td>${c.contact_person || '<span class="text-muted">-</span>'}</td>
            <td>
              <div class="small">${c.contact_phone || '-'}</div>
              <div class="small text-muted">${c.contact_email || ''}</div>
            </td>
            <td><code>${c.gst_number || '-'}</code></td>
            <td>
              <button class="btn btn-sm btn-outline-info" onclick="manageCompanyLocations('${c.id}', '${encodeURIComponent(c.name)}')">
                <i class="bi bi-geo-alt me-1"></i>${locCount} Depot(s)
              </button>
            </td>
            <td>
              <span class="badge ${c.is_active ? 'bg-success bg-opacity-25 text-success' : 'bg-secondary'}">
                ${c.is_active ? 'Active' : 'Inactive'}
              </span>
            </td>
            <td>
              <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary" data-min-role="fleet_manager" onclick='openEditCompanyModal(${JSON.stringify(c)})' title="Edit">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-outline-danger" data-min-role="fleet_manager" onclick="deleteCompany('${c.id}')" title="Delete">
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
    console.error('Error loading companies:', err);
    Utils.renderError(tableBody, 'Failed to fetch companies', () => loadCompanies());
  }
}

async function handleAddCompany(e) {
  e.preventDefault();
  const form = e.target;
  const name = document.getElementById('comp-name').value.trim();
  const person = document.getElementById('comp-person').value.trim();
  const email = document.getElementById('comp-email').value.trim();
  const phone = document.getElementById('comp-phone').value.trim();
  const gst = document.getElementById('comp-gst').value.trim();
  const notes = document.getElementById('comp-notes').value.trim();

  try {
    const payload = {
      name,
      contact_person: person || null,
      contact_email: email || null,
      contact_phone: phone || null,
      gst_number: gst || null,
      notes: notes || null,
    };

    const res = await ApiClient.post('/companies', payload);
    if (res.success) {
      Utils.showToast(`Company "${name}" registered successfully!`, 'success');
      const modalEl = document.getElementById('addCompanyModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      form.reset();
      loadCompanies();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to add company', 'danger');
  }
}

function openEditCompanyModal(c) {
  document.getElementById('edit-comp-id').value = c.id;
  document.getElementById('edit-comp-name').value = c.name;
  document.getElementById('edit-comp-person').value = c.contact_person || '';
  document.getElementById('edit-comp-email').value = c.contact_email || '';
  document.getElementById('edit-comp-phone').value = c.contact_phone || '';
  document.getElementById('edit-comp-gst').value = c.gst_number || '';
  document.getElementById('edit-comp-status').value = c.is_active ? 'true' : 'false';
  document.getElementById('edit-comp-notes').value = c.notes || '';

  const modal = new bootstrap.Modal(document.getElementById('editCompanyModal'));
  modal.show();
}

async function handleEditCompany(e) {
  e.preventDefault();
  const id = document.getElementById('edit-comp-id').value;
  const name = document.getElementById('edit-comp-name').value.trim();
  const person = document.getElementById('edit-comp-person').value.trim();
  const email = document.getElementById('edit-comp-email').value.trim();
  const phone = document.getElementById('edit-comp-phone').value.trim();
  const gst = document.getElementById('edit-comp-gst').value.trim();
  const isActive = document.getElementById('edit-comp-status').value === 'true';
  const notes = document.getElementById('edit-comp-notes').value.trim();

  try {
    const payload = {
      name,
      contact_person: person || null,
      contact_email: email || null,
      contact_phone: phone || null,
      gst_number: gst || null,
      is_active: isActive,
      notes: notes || null,
    };

    const res = await ApiClient.put(`/companies/${id}`, payload);
    if (res.success) {
      Utils.showToast('Company updated successfully!', 'success');
      const modalEl = document.getElementById('editCompanyModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      if (modal) modal.hide();
      loadCompanies();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to update company', 'danger');
  }
}

async function deleteCompany(id) {
  if (confirm('Are you sure you want to delete this company? All associated locations will be removed.')) {
    try {
      await ApiClient.delete(`/companies/${id}`);
      Utils.showToast('Company deleted successfully', 'success');
      loadCompanies();
    } catch (err) {
      Utils.showToast(err.message || 'Failed to delete company', 'danger');
    }
  }
}

async function manageCompanyLocations(companyId, companyName) {
  currentManagingCompanyId = companyId;
  const modalEl = document.getElementById('locationsModal');
  const modal = new bootstrap.Modal(modalEl);
  modal.show();

  document.getElementById('locations-modal-title').textContent = `Depots & Sites: ${decodeURIComponent(companyName)}`;
  loadCompanyLocationsList(companyId);
}

async function loadCompanyLocationsList(companyId) {
  const container = document.getElementById('locations-list-tbody');
  if (!container) return;

  container.innerHTML = '<tr><td colspan="5" class="text-center py-3 text-muted"><div class="spinner-border spinner-border-sm me-2"></div>Loading locations...</td></tr>';

  try {
    const res = await ApiClient.get(`/companies/${companyId}`);
    if (res.success && res.data) {
      const locs = res.data.locations || [];
      if (locs.length === 0) {
        container.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">No pickup/delivery locations registered yet.</td></tr>';
        return;
      }

      container.innerHTML = locs.map(l => `
        <tr>
          <td class="fw-bold text-white">${l.name}</td>
          <td><span class="badge bg-secondary text-uppercase">${l.location_type}</span></td>
          <td>${l.address || '-'}, ${l.city || ''}</td>
          <td><code>${l.latitude ? `${Number(l.latitude).toFixed(4)}, ${Number(l.longitude).toFixed(4)}` : 'N/A'}</code></td>
          <td>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteCompanyLocation('${companyId}', '${l.id}')">
              <i class="bi bi-trash"></i>
            </button>
          </td>
        </tr>
      `).join('');
    }
  } catch (err) {
    container.innerHTML = `<tr><td colspan="5" class="text-center text-danger py-3">${err.message}</td></tr>`;
  }
}

async function handleAddLocation(e) {
  e.preventDefault();
  if (!currentManagingCompanyId) return;

  const form = e.target;
  const name = document.getElementById('loc-name').value.trim();
  const address = document.getElementById('loc-address').value.trim();
  const city = document.getElementById('loc-city').value.trim();
  const state = document.getElementById('loc-state').value.trim();
  const lat = document.getElementById('loc-lat').value;
  const lng = document.getElementById('loc-lng').value;
  const type = document.getElementById('loc-type').value;

  try {
    const payload = {
      name,
      address: address || null,
      city: city || null,
      state: state || null,
      latitude: lat ? parseFloat(lat) : null,
      longitude: lng ? parseFloat(lng) : null,
      location_type: type,
    };

    const res = await ApiClient.post(`/companies/${currentManagingCompanyId}/locations`, payload);
    if (res.success) {
      Utils.showToast(`Location "${name}" added!`, 'success');
      form.reset();
      loadCompanyLocationsList(currentManagingCompanyId);
      loadCompanies();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to add location', 'danger');
  }
}

async function deleteCompanyLocation(companyId, locationId) {
  if (confirm('Delete this company depot?')) {
    try {
      await ApiClient.delete(`/companies/${companyId}/locations/${locationId}`);
      Utils.showToast('Location removed', 'success');
      loadCompanyLocationsList(companyId);
      loadCompanies();
    } catch (err) {
      Utils.showToast(err.message || 'Failed to delete location', 'danger');
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
