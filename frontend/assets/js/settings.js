/**
 * System Settings, Health/Readiness Probes, API Configuration, and User Profile.
 */
document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  // Populate current settings & profile
  loadApiConfig();
  loadUserProfile();

  // Probe API connection on load
  await checkApiHealth();

  const pingBtn = document.getElementById('btn-test-api');
  if (pingBtn) pingBtn.addEventListener('click', checkApiHealth);

  const saveApiBtn = document.getElementById('btn-save-api-url');
  if (saveApiBtn) saveApiBtn.addEventListener('click', handleSaveApiUrl);

  const profileForm = document.getElementById('user-profile-form');
  if (profileForm) profileForm.addEventListener('submit', handleUpdateProfile);
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

function loadApiConfig() {
  const urlInput = document.getElementById('setting-api-url');
  if (urlInput) {
    urlInput.value = CONFIG.API_BASE_URL;
  }
}

async function checkApiHealth() {
  const statusBadge = document.getElementById('api-health-badge');
  const latencyBadge = document.getElementById('api-latency-badge');
  const dbStatusBadge = document.getElementById('api-db-badge');
  const uptimeText = document.getElementById('api-uptime-text');

  if (statusBadge) {
    statusBadge.className = 'badge bg-warning text-dark';
    statusBadge.textContent = 'Pinging...';
  }

  const start = performance.now();

  try {
    const [healthRes, readyRes] = await Promise.all([
      ApiClient.get('/health'),
      ApiClient.get('/ready').catch(e => ({ success: false, message: e.message })),
    ]);

    const latency = Math.round(performance.now() - start);

    if (healthRes.status === 'healthy' || healthRes.success) {
      if (statusBadge) {
        statusBadge.className = 'badge bg-success';
        statusBadge.innerHTML = '<i class="bi bi-check-circle me-1"></i>Connected (200 OK)';
      }
      if (latencyBadge) {
        latencyBadge.textContent = `${latency} ms`;
        latencyBadge.className = `badge ${latency < 300 ? 'bg-success' : 'bg-warning text-dark'}`;
      }
      if (uptimeText) {
        uptimeText.textContent = `${Math.round(healthRes.uptime_seconds || 0)}s`;
      }
    } else {
      throw new Error(healthRes.message || 'Unhealthy response');
    }

    if (readyRes.status === 'ready' || readyRes.success) {
      if (dbStatusBadge) {
        dbStatusBadge.className = 'badge bg-success';
        dbStatusBadge.innerHTML = '<i class="bi bi-database-check me-1"></i>Reachable';
      }
    } else {
      if (dbStatusBadge) {
        dbStatusBadge.className = 'badge bg-danger';
        dbStatusBadge.innerHTML = '<i class="bi bi-database-exclamation me-1"></i>Unavailable';
      }
    }

    Utils.showToast(`Backend connection healthy (${latency}ms)`, 'success');
  } catch (err) {
    if (statusBadge) {
      statusBadge.className = 'badge bg-danger';
      statusBadge.innerHTML = '<i class="bi bi-x-circle me-1"></i>Disconnected';
    }
    if (latencyBadge) latencyBadge.textContent = 'Timeout';
    if (dbStatusBadge) dbStatusBadge.textContent = 'Unknown';
    Utils.showToast(`Failed to reach backend at ${CONFIG.API_BASE_URL}`, 'danger');
  }
}

function handleSaveApiUrl() {
  const urlInput = document.getElementById('setting-api-url');
  if (!urlInput) return;

  const newUrl = urlInput.value.trim();
  if (!newUrl) {
    CONFIG.API_BASE_URL = '';
    Utils.showToast('Reset to default API URL', 'info');
  } else {
    CONFIG.API_BASE_URL = newUrl;
    Utils.showToast(`Saved API Base URL: ${newUrl}`, 'success');
  }

  checkApiHealth();
}

function setApiPreset(url) {
  const input = document.getElementById('setting-api-url');
  if (input) {
    input.value = url;
    handleSaveApiUrl();
  }
}

async function loadUserProfile() {
  try {
    const res = await ApiClient.get('/auth/me');
    if (res.success && res.data) {
      const u = res.data;
      document.getElementById('profile-first-name').value = u.first_name || '';
      document.getElementById('profile-last-name').value = u.last_name || '';
      document.getElementById('profile-email').value = u.email || '';
      document.getElementById('profile-role').value = (u.role || '').toUpperCase();
    }
  } catch (err) {
    console.error('Error fetching profile:', err);
  }
}

async function handleUpdateProfile(e) {
  e.preventDefault();
  const firstName = document.getElementById('profile-first-name').value.trim();
  const lastName = document.getElementById('profile-last-name').value.trim();
  const password = document.getElementById('profile-new-password').value;

  try {
    const payload = {
      first_name: firstName,
      last_name: lastName,
    };
    if (password && password.trim()) {
      if (password.length < 8) {
        Utils.showToast('New password must be at least 8 characters', 'warning');
        return;
      }
      payload.password = password.trim();
    }

    const res = await ApiClient.put('/auth/me', payload);
    if (res.success && res.data) {
      Utils.showToast('User profile updated successfully!', 'success');
      localStorage.setItem(CONFIG.STORAGE_KEYS.USER_DATA, JSON.stringify(res.data));
      Auth.initUI();
      document.getElementById('profile-new-password').value = '';
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to update profile', 'danger');
  }
}
