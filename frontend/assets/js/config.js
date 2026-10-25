/**
 * Application Runtime & Public Configuration.
 * 
 * PUBLIC CONFIGURATION INSTRUCTIONS:
 * 1. For Production Deployment (Vercel):
 *    Replace the PRODUCTION_API_URL placeholder below with your actual deployed Railway backend URL:
 *    e.g., 'https://<YOUR_RAILWAY_APP>.up.railway.app/api/v1'
 * 
 * 2. Runtime Override:
 *    Users or testers can also override the API URL dynamically from the System Settings page
 *    (stored locally in browser localStorage without requiring a redeployment).
 */
const PUBLIC_CONFIG = {
  // Public production backend API on Render:
  PRODUCTION_API_URL: 'https://transport-gps-tracking.onrender.com/api/v1',
  LOCAL_API_URL: 'http://localhost:5000/api/v1',
  POLL_INTERVAL_MS: 4000,
  MAP_DEFAULT_CENTER: [19.0760, 72.8777], // Mumbai / JNPT Freight Corridor
  MAP_DEFAULT_ZOOM: 11
};

const CONFIG = {
  get API_BASE_URL() {
    const customUrl = localStorage.getItem('tgt_api_base_url');
    if (customUrl && customUrl.trim()) {
      return customUrl.trim().replace(/\/+$/, '');
    }
    const isLocalhost = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
    return isLocalhost ? PUBLIC_CONFIG.LOCAL_API_URL : PUBLIC_CONFIG.PRODUCTION_API_URL;
  },

  set API_BASE_URL(url) {
    if (url && url.trim()) {
      localStorage.setItem('tgt_api_base_url', url.trim().replace(/\/+$/, ''));
    } else {
      localStorage.removeItem('tgt_api_base_url');
    }
  },

  POLL_INTERVAL_MS: PUBLIC_CONFIG.POLL_INTERVAL_MS,
  MAP_DEFAULT_CENTER: PUBLIC_CONFIG.MAP_DEFAULT_CENTER,
  MAP_DEFAULT_ZOOM: PUBLIC_CONFIG.MAP_DEFAULT_ZOOM,

  // Local storage keys
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'tgt_access_token',
    REFRESH_TOKEN: 'tgt_refresh_token',
    USER_DATA: 'tgt_user_data',
    API_URL_OVERRIDE: 'tgt_api_base_url'
  }
};
