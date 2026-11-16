/**
 * Shared formatting, feedback indicators, and UI helper utilities.
 */
const Utils = {
  formatDate(isoString) {
    if (!isoString) return 'N/A';
    try {
      let str = String(isoString).trim();
      if (!str.endsWith('Z') && !str.includes('+') && !str.slice(10).includes('-')) {
        str += 'Z';
      }
      const d = new Date(str);
      return isNaN(d.getTime()) ? isoString : d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return isoString;
    }
  },

  formatDuration(minutes) {
    if (minutes === null || minutes === undefined) return '0 min';
    const totalMin = Math.round(Number(minutes));
    if (totalMin < 60) return `${totalMin} min`;
    const hrs = Math.floor(totalMin / 60);
    const mins = totalMin % 60;
    return `${hrs}h ${mins}m`;
  },

  formatSpeed(speedKmh) {
    if (speedKmh === null || speedKmh === undefined) return '0.0 km/h';
    return `${Number(speedKmh).toFixed(1)} km/h`;
  },

  formatDistance(km) {
    if (km === null || km === undefined) return '0.0 km';
    return `${Number(km).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} km`;
  },

  formatFuel(litres) {
    if (litres === null || litres === undefined) return 'N/A';
    return `${Number(litres).toFixed(1)} L`;
  },

  getStatusBadge(status, isOnline = null) {
    const s = (status || 'offline').toLowerCase();

    // If explicit offline status or isOnline is false
    if (isOnline === false || s === 'offline') {
      return `<span class="status-badge status-offline">Offline</span>`;
    }

    // Active, online, or isOnline is true -> Online (Connected)
    if (isOnline === true || s === 'active' || s === 'online') {
      return `<span class="status-badge status-online">Online</span>`;
    }

    // Stationary with tracker connected
    if (s === 'idle') {
      return `<span class="status-badge status-idle">Online (Idle)</span>`;
    }

    // Fleet Maintenance
    if (s === 'maintenance') {
      return `<span class="status-badge status-maintenance">Maintenance</span>`;
    }

    return `<span class="status-badge status-${s}">${s}</span>`;
  },

  getLoadStatusBadge(loadStatus) {
    const isLoaded = (loadStatus || 'empty').toLowerCase() === 'loaded';
    if (isLoaded) {
      return `<span class="badge bg-primary bg-opacity-75 text-white px-2 py-1"><i class="bi bi-box-seam me-1"></i>Loaded</span>`;
    }
    return `<span class="badge bg-secondary bg-opacity-50 text-light px-2 py-1"><i class="bi bi-dash-circle me-1"></i>Empty</span>`;
  },

  getAlertBadge(severity) {
    const sev = (severity || 'info').toLowerCase();
    const map = {
      critical: 'danger',
      warning: 'warning text-dark',
      info: 'info text-dark',
      low: 'secondary',
    };
    return `<span class="badge bg-${map[sev] || 'secondary'} text-uppercase">${sev}</span>`;
  },

  /**
   * Floating Toast Notifications
   */
  showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
      container.style.zIndex = '9999';
      document.body.appendChild(container);
    }

    const toastEl = document.createElement('div');
    const bgClass = type === 'success' ? 'bg-success' : type === 'danger' ? 'bg-danger' : type === 'warning' ? 'bg-warning text-dark' : 'bg-primary';
    toastEl.className = `toast align-items-center text-white ${bgClass} border-0 show shadow-lg mb-2`;
    toastEl.setAttribute('role', 'alert');
    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body fw-medium">${message}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;
    container.appendChild(toastEl);

    setTimeout(() => {
      toastEl.classList.remove('show');
      setTimeout(() => toastEl.remove(), 300);
    }, 4000);
  },

  renderLoading(container, text = 'Loading records...') {
    if (!container) return;
    container.innerHTML = `
      <div class="text-center py-5 text-muted">
        <div class="spinner-border text-primary mb-3" role="status" style="width: 2.2rem; height: 2.2rem;"></div>
        <div class="small fw-semibold text-uppercase letter-spacing-1">${text}</div>
      </div>
    `;
  },

  renderEmptyState(container, message = 'No records found', icon = 'bi-inbox') {
    if (!container) return;
    container.innerHTML = `
      <div class="text-center py-5 text-muted">
        <i class="bi ${icon} display-4 opacity-50 mb-3 d-block"></i>
        <div class="fw-semibold">${message}</div>
      </div>
    `;
  },

  renderError(container, message = 'Failed to load data from backend', onRetry = null) {
    if (!container) return;
    const retryBtn = onRetry ? `<button class="btn btn-sm btn-outline-primary mt-3 retry-btn"><i class="bi bi-arrow-clockwise me-1"></i>Try Again</button>` : '';
    container.innerHTML = `
      <div class="text-center py-5 text-danger">
        <i class="bi bi-exclamation-triangle-fill display-5 opacity-75 mb-2 d-block"></i>
        <div class="fw-semibold">${message}</div>
        ${retryBtn}
      </div>
    `;
    if (onRetry) {
      container.querySelector('.retry-btn')?.addEventListener('click', onRetry);
    }
  }
};

/**
 * ThemeManager - Manages Dark and Light theme switching and persistence across pages.
 */
const ThemeManager = {
  STORAGE_KEY: 'tgt_theme',

  getTheme() {
    try {
      return localStorage.getItem(this.STORAGE_KEY) || 'dark';
    } catch (e) {
      return 'dark';
    }
  },

  setTheme(theme) {
    const isLight = theme === 'light';
    const targetTheme = isLight ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-bs-theme', targetTheme);
    document.documentElement.setAttribute('data-theme', targetTheme);
    
    try {
      localStorage.setItem(this.STORAGE_KEY, targetTheme);
    } catch (e) {
      console.warn('Could not persist theme in localStorage', e);
    }

    this.updateButtons(targetTheme);
    window.dispatchEvent(new CustomEvent('tgt_theme_changed', { detail: { theme: targetTheme } }));
  },

  toggle() {
    const current = this.getTheme();
    const next = current === 'light' ? 'dark' : 'light';
    this.setTheme(next);
    return next;
  },

  updateButtons(theme) {
    const isLight = theme === 'light';
    const buttons = document.querySelectorAll('.theme-toggle-btn, #theme-toggle-btn');
    buttons.forEach((btn) => {
      btn.setAttribute('title', isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode');
      btn.setAttribute('aria-label', isLight ? 'Switch to Dark Mode' : 'Switch to Light Mode');
      btn.innerHTML = isLight 
        ? '<i class="bi bi-moon-stars-fill text-primary" style="font-size:1.1rem;"></i>' 
        : '<i class="bi bi-sun-fill text-warning" style="font-size:1.1rem;"></i>';
    });
  },

  bindButtons() {
    // Auto-inject into .topbar-actions if no theme button is present on the page
    const topbarActions = document.querySelector('.topbar-actions');
    if (topbarActions && !document.querySelector('.theme-toggle-btn, #theme-toggle-btn')) {
      const toggleBtn = document.createElement('button');
      toggleBtn.type = 'button';
      toggleBtn.id = 'theme-toggle-btn';
      toggleBtn.className = 'theme-toggle-btn';
      // Insert right before logout or at the start
      const logoutBtn = topbarActions.querySelector('.btn-logout');
      if (logoutBtn) {
        topbarActions.insertBefore(toggleBtn, logoutBtn);
      } else {
        topbarActions.appendChild(toggleBtn);
      }
    }

    const buttons = document.querySelectorAll('.theme-toggle-btn, #theme-toggle-btn');
    buttons.forEach((btn) => {
      if (btn.dataset.themeBound) return;
      btn.dataset.themeBound = 'true';
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        this.toggle();
      });
    });

    this.updateButtons(this.getTheme());
  },

  init() {
    const theme = this.getTheme();
    document.documentElement.setAttribute('data-bs-theme', theme);
    document.documentElement.setAttribute('data-theme', theme);

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.bindButtons());
    } else {
      this.bindButtons();
    }
  }
};

// Expose globally and on Utils
window.ThemeManager = ThemeManager;
Utils.ThemeManager = ThemeManager;
ThemeManager.init();
