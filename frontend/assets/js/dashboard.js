/**
 * Dashboard KPIs, dynamic Chart.js visualizations, and live summary roster.
 */
let fleetChartInstance = null;
let activityChartInstance = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();

  // Mobile sidebar toggle handler
  setupMobileSidebar();

  // Load dashboard data
  await loadDashboardMetrics();
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

async function loadDashboardMetrics() {
  const kpiSection = document.getElementById('kpi-section');

  try {
    const [summaryRes, alertsRes, liveRes] = await Promise.all([
      ApiClient.get('/analytics/summary').catch(e => ({ error: e.message })),
      ApiClient.get('/alerts?limit=5&status=unacknowledged').catch(e => ({ error: e.message })),
      ApiClient.get('/gps/live').catch(e => ({ error: e.message }))
    ]);

    if (summaryRes.success && summaryRes.data) {
      renderKPIs(summaryRes.data);
      renderFleetStatusChart(summaryRes.data.fleet);
    }

    if (alertsRes.success && alertsRes.data) {
      renderRecentAlerts(alertsRes.data);
    } else {
      const container = document.getElementById('recent-alerts-list');
      if (container) container.innerHTML = '<div class="text-muted p-4 text-center">No active alerts reported.</div>';
    }

    if (liveRes.success && liveRes.data) {
      renderLiveFleetTable(liveRes.data.slice(0, 5));
      renderSpeedActivityChart(liveRes.data);
    }
  } catch (err) {
    console.error('Error loading dashboard data:', err);
    Utils.showToast('Could not load some dashboard metrics', 'danger');
  }
}

function renderKPIs(data) {
  const fleet = data.fleet || {};
  const elTotal = document.getElementById('kpi-total-vehicles');
  const elActive = document.getElementById('kpi-active-vehicles');
  const elIdle = document.getElementById('kpi-idle-vehicles');
  const elMaint = document.getElementById('kpi-maint-vehicles');
  const elAlerts = document.getElementById('kpi-alerts-count');
  const elDist = document.getElementById('kpi-total-distance');
  const elTrips = document.getElementById('kpi-total-trips');

  if (elTotal) elTotal.textContent = fleet.total_vehicles || 0;
  if (elActive) elActive.textContent = fleet.active || 0;
  if (elIdle) elIdle.textContent = fleet.idle || 0;
  if (elMaint) elMaint.textContent = fleet.maintenance || 0;
  if (elAlerts) elAlerts.textContent = data.alerts?.unacknowledged || 0;
  if (elDist) elDist.textContent = Utils.formatDistance(data.total_fleet_km || 0);
  if (elTrips) elTrips.textContent = data.trips?.total_recorded || 0;
}

function renderFleetStatusChart(fleet = {}) {
  const ctx = document.getElementById('fleetStatusChart');
  if (!ctx) return;

  const active = fleet.active || 0;
  const idle = fleet.idle || 0;
  const maintenance = fleet.maintenance || 0;
  const offline = fleet.offline || 0;

  if (fleetChartInstance) fleetChartInstance.destroy();

  fleetChartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Active', 'Idle', 'Maintenance', 'Offline'],
      datasets: [{
        data: [active, idle, maintenance, offline],
        backgroundColor: ['#10B981', '#F59E0B', '#8B5CF6', '#64748B'],
        borderWidth: 2,
        borderColor: '#111827',
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#9CA3AF', font: { family: 'Outfit', size: 12 }, padding: 16 }
        }
      },
      cutout: '72%',
    }
  });
}

function renderSpeedActivityChart(liveVehicles = []) {
  const ctx = document.getElementById('speedDistributionChart');
  if (!ctx) return;

  const labels = liveVehicles.map(v => v.registration_number || 'Truck');
  const speeds = liveVehicles.map(v => Number(v.speed_kmh || 0));

  if (activityChartInstance) activityChartInstance.destroy();

  activityChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels.length ? labels : ['No Data'],
      datasets: [{
        label: 'Current Speed (km/h)',
        data: speeds.length ? speeds : [0],
        backgroundColor: 'rgba(59, 130, 246, 0.7)',
        borderRadius: 6,
        borderWidth: 0,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { grid: { display: false }, ticks: { color: '#9CA3AF', font: { family: 'Outfit', size: 11 } } },
        y: { grid: { color: 'rgba(255, 255, 255, 0.05)' }, ticks: { color: '#9CA3AF' }, beginAtZero: true }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

function renderRecentAlerts(alerts) {
  const container = document.getElementById('recent-alerts-list');
  if (!container) return;

  if (!alerts || alerts.length === 0) {
    container.innerHTML = '<div class="text-muted p-4 text-center"><i class="bi bi-shield-check text-success fs-3 d-block mb-1"></i>No unacknowledged alerts. All systems operational.</div>';
    return;
  }

  container.innerHTML = alerts.map(a => `
    <div class="d-flex align-items-center justify-content-between p-3 border-bottom border-secondary border-opacity-10">
      <div class="d-flex align-items-start gap-3">
        <div class="mt-1">${Utils.getAlertBadge(a.severity)}</div>
        <div>
          <div class="fw-semibold text-white">${a.registration_number || 'Fleet Vehicle'} &bull; <span class="text-info">${a.alert_type}</span></div>
          <small class="text-muted">${a.message}</small>
          <div class="small text-dim mt-1">${Utils.formatDate(a.created_at)}</div>
        </div>
      </div>
      <div>
        <button class="btn btn-sm btn-outline-warning" onclick="quickAcknowledgeAlert('${a.id}')">
          <i class="bi bi-check-lg"></i> Acknowledge
        </button>
      </div>
    </div>
  `).join('');
}

async function quickAcknowledgeAlert(alertId) {
  try {
    await ApiClient.post(`/alerts/${alertId}/acknowledge`, {});
    Utils.showToast('Alert acknowledged successfully', 'success');
    loadDashboardMetrics();
  } catch (err) {
    Utils.showToast(err.message || 'Failed to acknowledge alert', 'danger');
  }
}

function renderLiveFleetTable(vehicles) {
  const tbody = document.getElementById('dashboard-live-tbody');
  if (!tbody) return;

  if (!vehicles || vehicles.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No live vehicle telemetry received yet.</td></tr>';
    return;
  }

  tbody.innerHTML = vehicles.map(v => `
    <tr>
      <td class="fw-bold text-white">
        <a href="/live-tracking.html?focus=${v.vehicle_id}" class="text-info text-decoration-none">
          <i class="bi bi-truck me-2"></i>${v.registration_number}
        </a>
      </td>
      <td>${v.driver_name || '<span class="text-muted">Unassigned</span>'}</td>
      <td>${Utils.getStatusBadge(v.status)}</td>
      <td><code>${Utils.formatSpeed(v.speed_kmh)}</code></td>
      <td><small class="text-muted">${Utils.formatDate(v.last_updated)}</small></td>
    </tr>
  `).join('');
}
