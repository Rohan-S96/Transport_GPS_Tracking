/**
 * Alert Monitoring, Safety Triage, and Incident Acknowledgment.
 */
document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  await loadAlerts();

  const statusFilter = document.getElementById('alert-filter-status');
  const severityFilter = document.getElementById('alert-filter-severity');

  if (statusFilter) statusFilter.addEventListener('change', () => loadAlerts());
  if (severityFilter) severityFilter.addEventListener('change', () => loadAlerts());

  const simForm = document.getElementById('trigger-alert-form');
  if (simForm) simForm.addEventListener('submit', handleTriggerSimulatedAlert);
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

async function loadAlerts() {
  const tableBody = document.getElementById('alerts-table-body');
  if (!tableBody) return;

  const status = document.getElementById('alert-filter-status')?.value || '';
  const severity = document.getElementById('alert-filter-severity')?.value || '';

  Utils.renderLoading(tableBody, 'Scanning safety incident feed...');

  try {
    let endpoint = '/alerts?limit=50';
    if (status) endpoint += `&status=${encodeURIComponent(status)}`;
    if (severity) endpoint += `&severity=${encodeURIComponent(severity)}`;

    const res = await ApiClient.get(endpoint);
    if (res.success && Array.isArray(res.data)) {
      if (res.data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted py-5"><i class="bi bi-shield-check display-6 d-block mb-2 text-success opacity-75"></i>No incident alerts found for the selected criteria.</td></tr>';
        return;
      }

      tableBody.innerHTML = res.data.map(a => {
        const speedText = a.speed_kmh ? Utils.formatSpeed(a.speed_kmh) : '-';
        return `
          <tr>
            <td>
              <span class="badge bg-secondary bg-opacity-50 text-white font-monospace">
                ${a.alert_type}
              </span>
            </td>
            <td class="fw-bold text-white">
              <i class="bi bi-truck text-primary me-1"></i>${a.registration_number || 'N/A'}
            </td>
            <td>${Utils.getAlertBadge(a.severity)}</td>
            <td class="small text-light">${a.message}</td>
            <td><code>${speedText}</code></td>
            <td class="small text-muted">${Utils.formatDate(a.created_at)}</td>
            <td>
              ${a.is_acknowledged 
                ? '<span class="text-success small fw-semibold"><i class="bi bi-check2-all me-1"></i>Acknowledged</span>' 
                : `<button class="btn btn-sm btn-outline-warning" onclick="acknowledgeAlert('${a.id}')">
                    <i class="bi bi-check-lg me-1"></i>Acknowledge
                   </button>`}
            </td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error loading alerts:', err);
    Utils.renderError(tableBody, 'Failed to fetch alerts from server', () => loadAlerts());
  }
}

async function acknowledgeAlert(alertId) {
  try {
    const res = await ApiClient.post(`/alerts/${alertId}/acknowledge`, {});
    if (res.success) {
      Utils.showToast('Incident acknowledged and logged in audit history', 'success');
      loadAlerts();
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to acknowledge alert', 'danger');
  }
}

async function handleTriggerSimulatedAlert(e) {
  e.preventDefault();
  // We can trigger an overspeed telemetry packet via GPS locations
  const truckId = document.getElementById('sim-alert-truck').value;
  const type = document.getElementById('sim-alert-type').value;

  try {
    // We send high speed to trigger real overspeed alert in TrackingService
    const res = await ApiClient.post('/gps/locations', {
      vehicle_id: truckId,
      latitude: 19.0760,
      longitude: 72.8777,
      speed_kmh: type === 'overspeed' ? 120.0 : 40.0,
      ignition: true,
    });

    if (res.success) {
      Utils.showToast('Simulated event dispatched!', 'success');
      const modal = bootstrap.Modal.getInstance(document.getElementById('simAlertModal'));
      if (modal) modal.hide();
      setTimeout(loadAlerts, 1000);
    }
  } catch (err) {
    Utils.showToast(err.message || 'Failed to dispatch test event', 'danger');
  }
}
