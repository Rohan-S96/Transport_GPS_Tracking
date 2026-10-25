/**
 * System User Management and Role-Based Access Control (RBAC).
 */
document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  await loadUsers();

  const addForm = document.getElementById('add-user-form');
  if (addForm) addForm.addEventListener('submit', handleAddUser);

  const editForm = document.getElementById('edit-user-form');
  if (editForm) editForm.addEventListener('submit', handleEditUser);

  const searchInput = document.getElementById('user-search');
  if (searchInput) searchInput.addEventListener('input', debounce(() => loadUsers(), 300));
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

async function loadUsers() {
  const tableBody = document.getElementById('users-table-body');
  if (!tableBody) return;

  const search = document.getElementById('user-search')?.value.trim() || '';
  Utils.renderLoading(tableBody, 'Loading organisation users...');

  try {
    let endpoint = '/users?limit=50';
    if (search) endpoint += `&search=${encodeURIComponent(search)}`;

    const res = await ApiClient.get(endpoint);
    if (res.success && Array.isArray(res.data)) {
      if (res.data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-5"><i class="bi bi-people display-6 d-block mb-2 opacity-50"></i>No users found.</td></tr>';
        return;
      }

      tableBody.innerHTML = res.data.map(u => {
        const roleBadges = {
          admin: '<span class="badge bg-danger text-uppercase px-2 py-1"><i class="bi bi-shield-lock me-1"></i>Admin</span>',
          fleet_manager: '<span class="badge bg-primary text-uppercase px-2 py-1"><i class="bi bi-person-gear me-1"></i>Fleet Manager</span>',
          driver: '<span class="badge bg-warning text-dark text-uppercase px-2 py-1"><i class="bi bi-truck me-1"></i>Driver</span>',
          viewer: '<span class="badge bg-secondary text-uppercase px-2 py-1"><i class="bi bi-eye me-1"></i>Viewer</span>',
        };

        return `
          <tr>
            <td class="fw-bold text-white">
              <i class="bi bi-person-circle text-info me-2"></i>${u.full_name || `${u.first_name} ${u.last_name}`}
            </td>
            <td><code>${u.email}</code></td>
            <td>${roleBadges[u.role] || u.role}</td>
            <td>
              <span class="badge ${u.is_active ? 'bg-success bg-opacity-25 text-success' : 'bg-secondary'}">
                ${u.is_active ? 'Active' : 'Deactivated'}
              </span>
            </td>
            <td class="small text-muted">${u.last_login_at ? Utils.formatDate(u.last_login_at) : 'Never'}</td>
            <td>
              <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary" data-min-role="admin" onclick='openEditUserModal(${JSON.stringify(u)})' title="Edit">
                  <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-outline-danger" data-min-role="admin" onclick="deleteUser('${u.id}')" title="Deactivate">
                  <i class="bi bi-slash-circle"></i>
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');

      Auth.initUI();
    }
  } catch (err) {
    console.error('Error loading users:', err);
    Utils.renderError(tableBody, 'Failed to fetch user directory', () => loadUsers());
  }
}

async function handleAddUser(e) {
  e.preventDefault();
  const form = e.target;
  const firstName = document.getElementById('user-first-name').value.trim();
  const lastName = document.getElementById('user-last-name').value.trim();
  const email = document.getElementById('user-email').value.trim();
  const password = document.getElementById('user-password').value;
  const role = document.getElementById('user-role').value;

  try {
    const payload = {
      first_name: firstName,
      last_name: lastName,
      email,
      password,
      role,
    };

    const res = await ApiClient.post('/users', payload);
    if (res.success) {
      Utils.showToast(`User ${email} created successfully!`, 'success');
      const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
      if (modal) modal.hide();
      form.reset();
      loadUsers();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to create user', 'danger');
  }
}

function openEditUserModal(u) {
  document.getElementById('edit-user-id').value = u.id;
  document.getElementById('edit-user-name').value = `${u.first_name || ''} ${u.last_name || ''}`.trim();
  document.getElementById('edit-user-email').value = u.email;
  document.getElementById('edit-user-role').value = u.role || 'viewer';
  document.getElementById('edit-user-status').value = u.is_active ? 'true' : 'false';

  const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
  modal.show();
}

async function handleEditUser(e) {
  e.preventDefault();
  const id = document.getElementById('edit-user-id').value;
  const role = document.getElementById('edit-user-role').value;
  const isActive = document.getElementById('edit-user-status').value === 'true';
  const newPassword = document.getElementById('edit-user-password').value;

  try {
    const payload = {
      role,
      is_active: isActive,
    };
    if (newPassword && newPassword.trim()) {
      payload.password = newPassword.trim();
    }

    const res = await ApiClient.put(`/users/${id}`, payload);
    if (res.success) {
      Utils.showToast('User permissions updated successfully!', 'success');
      const modal = bootstrap.Modal.getInstance(document.getElementById('editUserModal'));
      if (modal) modal.hide();
      loadUsers();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to update user', 'danger');
  }
}

async function deleteUser(id) {
  if (confirm('Deactivate this user account? They will no longer be able to log in.')) {
    try {
      await ApiClient.delete(`/users/${id}`);
      Utils.showToast('User deactivated', 'success');
      loadUsers();
    } catch (err) {
      Utils.showToast(err.message || 'Failed to deactivate user', 'danger');
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
