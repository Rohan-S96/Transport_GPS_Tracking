/**
 * Fleet Analytics, Statistical Reports, and Excel/CSV Export Engine.
 */
document.addEventListener('DOMContentLoaded', async () => {
  if (!Auth.requireAuth()) return;
  Auth.initUI();
  setupMobileSidebar();

  await loadReportSummary();
  setupExportButtons();
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

async function loadReportSummary() {
  try {
    const res = await ApiClient.get('/analytics/summary');
    if (res.success && res.data) {
      const fleet = res.data.fleet || {};
      const elVehicles = document.getElementById('rep-total-vehicles');
      const elTrips = document.getElementById('rep-total-trips');
      const elDistance = document.getElementById('rep-total-distance');
      const elAlerts = document.getElementById('rep-total-alerts');

      if (elVehicles) elVehicles.textContent = fleet.total_vehicles || 0;
      if (elTrips) elTrips.textContent = res.data.trips?.total_recorded || 0;
      if (elDistance) elDistance.textContent = Utils.formatDistance(res.data.total_fleet_km || 0);
      if (elAlerts) elAlerts.textContent = res.data.alerts?.unacknowledged || 0;
    }
  } catch (err) {
    console.error('Failed to load report summary metrics:', err);
  }
}

function setupExportButtons() {
  const btnVehiclesExcel = document.getElementById('btn-export-vehicles-excel');
  const btnVehiclesCsv = document.getElementById('btn-export-vehicles-csv');
  const btnTripsExcel = document.getElementById('btn-export-trips-excel');
  const btnTripsCsv = document.getElementById('btn-export-trips-csv');

  if (btnVehiclesExcel) {
    btnVehiclesExcel.addEventListener('click', () => handleExport('vehicles', 'excel', btnVehiclesExcel));
  }
  if (btnVehiclesCsv) {
    btnVehiclesCsv.addEventListener('click', () => handleExport('vehicles', 'csv', btnVehiclesCsv));
  }
  if (btnTripsExcel) {
    btnTripsExcel.addEventListener('click', () => handleExport('trips', 'excel', btnTripsExcel));
  }
  if (btnTripsCsv) {
    btnTripsCsv.addEventListener('click', () => handleExport('trips', 'csv', btnTripsCsv));
  }
}

async function handleExport(type, format, buttonEl) {
  const originalHtml = buttonEl.innerHTML;
  buttonEl.disabled = true;
  buttonEl.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Generating...';

  try {
    const filename = `${type}_export_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : 'csv'}`;
    Utils.showToast(`Building ${type} report (${format.toUpperCase()})...`, 'info');

    const downloadedName = await ApiClient.downloadFile(
      `/analytics/export?type=${type}&format=${format}`,
      filename
    );

    Utils.showToast(`Export complete: ${downloadedName}`, 'success');
  } catch (err) {
    Utils.showToast(err.message || 'Export failed. Ensure backend has records and openpyxl is installed.', 'danger');
  } finally {
    buttonEl.disabled = false;
    buttonEl.innerHTML = originalHtml;
  }
}
