/**
 * Authentication handling, session guards, and Role-Based Access Control (RBAC).
 */
const ROLE_HIERARCHY = {
  viewer: 1,
  driver: 2,
  fleet_manager: 3,
  admin: 4,
};

const Auth = {
  isAuthenticated() {
    return !!ApiClient.getToken();
  },

  getCurrentUser() {
    const raw = localStorage.getItem(CONFIG.STORAGE_KEYS.USER_DATA);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  getUserRole() {
    const user = this.getCurrentUser();
    return user ? (user.role || 'viewer') : 'viewer';
  },

  hasMinRole(minRole) {
    const current = this.getUserRole();
    const userLevel = ROLE_HIERARCHY[current] || 0;
    const requiredLevel = ROLE_HIERARCHY[minRole] || 99;
    return userLevel >= requiredLevel;
  },

  requireAuth() {
    if (!this.isAuthenticated()) {
      const current = window.location.pathname;
      if (!current.includes('login.html')) {
        window.location.href = '/login.html';
      }
      return false;
    }
    return true;
  },

  redirectIfAuthenticated() {
    if (this.isAuthenticated()) {
      window.location.href = '/index.html';
    }
  },

  async login(email, password) {
    const res = await ApiClient.post('/auth/login', { email, password });
    if (res.success && res.data) {
      ApiClient.setToken(res.data.access_token, res.data.refresh_token);
      localStorage.setItem(CONFIG.STORAGE_KEYS.USER_DATA, JSON.stringify(res.data.user));
      return res.data;
    }
    throw new Error(res.message || 'Login failed');
  },

  async register(payload) {
    return await ApiClient.post('/auth/register', payload);
  },

  logout() {
    ApiClient.clearSession();
    window.location.href = '/login.html';
  },

  /**
   * Initializes user information in the UI and applies RBAC rules to elements
   * marked with data-min-role="admin" or data-min-role="fleet_manager".
   */
  initUI() {
    const user = this.getCurrentUser();
    if (!user) return;

    // Populate user displays
    document.querySelectorAll('.current-user-name').forEach(el => {
      el.textContent = user.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email;
    });

    document.querySelectorAll('.current-user-email').forEach(el => {
      el.textContent = user.email || '';
    });

    document.querySelectorAll('.current-user-role').forEach(el => {
      el.textContent = (user.role || 'viewer').replace('_', ' ').toUpperCase();
    });

    // Enforce role-based element permissions
    const userLevel = ROLE_HIERARCHY[user.role || 'viewer'] || 1;
    document.querySelectorAll('[data-min-role]').forEach(el => {
      const requiredRole = el.getAttribute('data-min-role');
      const requiredLevel = ROLE_HIERARCHY[requiredRole] || 99;
      if (userLevel < requiredLevel) {
        if (el.tagName === 'BUTTON' || el.tagName === 'INPUT' || el.tagName === 'SELECT') {
          el.disabled = true;
          el.title = `Requires ${requiredRole} permissions`;
          el.classList.add('opacity-50');
        } else {
          el.style.display = 'none';
        }
      }
    });

    // Wire up all logout buttons
    document.querySelectorAll('.btn-logout').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        Auth.logout();
      });
    });
  }
};
