/**
 * Leaflet & OpenStreetMap Engine for Fleet GPS Tracking and Route Playback.
 */
class FleetMap {
  constructor(containerId = 'fleet-map', options = {}) {
    this.containerId = containerId;
    this.center = options.center || CONFIG.MAP_DEFAULT_CENTER;
    this.zoom = options.zoom || CONFIG.MAP_DEFAULT_ZOOM;
    this.map = null;
    this.markers = new Map(); // vehicleId -> L.marker
    this.geofenceLayers = new Map();
    this.historyPolyline = null;
    this.startMarker = null;
    this.endMarker = null;
    this.playbackMarker = null;
    this.stopMarkers = [];
    this.init();
  }

  init() {
    const el = document.getElementById(this.containerId);
    if (!el) return;

    // Initialize Leaflet map
    this.map = L.map(this.containerId, {
      zoomControl: false,
    }).setView(this.center, this.zoom);

    // Zoom control at bottom right
    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    // High performance OpenStreetMap Tile Layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(this.map);
  }

  createVehicleIcon(status = 'active', heading = 0) {
    return L.divIcon({
      className: 'custom-vehicle-marker',
      html: `
        <div class="marker-pulse"></div>
        <div class="marker-pin ${status.toLowerCase()}" style="transform: rotate(${heading}deg);">
          <i class="bi bi-truck-front-fill"></i>
        </div>
      `,
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    });
  }

  updateVehicleMarker(vehicle) {
    if (!this.map || !vehicle.latitude || !vehicle.longitude) return;

    const vId = vehicle.vehicle_id || vehicle.id;
    const latLng = [vehicle.latitude, vehicle.longitude];
    const icon = this.createVehicleIcon(vehicle.status, vehicle.heading || 0);

    const popupHtml = `
      <div class="vehicle-popup-card">
        <div class="vehicle-popup-header">
          <div class="vehicle-popup-reg">${vehicle.registration_number || 'Vehicle'}</div>
          ${Utils.getStatusBadge(vehicle.status)}
        </div>
        <div class="vehicle-popup-stat">
          <span>Driver</span>
          <span>${vehicle.driver_name || (vehicle.assigned_driver ? vehicle.assigned_driver.name : 'Unassigned')}</span>
        </div>
        <div class="vehicle-popup-stat">
          <span>Speed</span>
          <span>${Utils.formatSpeed(vehicle.speed_kmh || (vehicle.last_known_telemetry ? vehicle.last_known_telemetry.speed_kmh : 0))}</span>
        </div>
        <div class="vehicle-popup-stat">
          <span>Battery</span>
          <span>${vehicle.battery_pct || 100}%</span>
        </div>
        <div class="vehicle-popup-stat">
          <span>Last Seen</span>
          <span>${Utils.formatDate(vehicle.last_updated || (vehicle.last_known_telemetry ? vehicle.last_known_telemetry.recorded_at : ''))}</span>
        </div>
      </div>
    `;

    if (this.markers.has(vId)) {
      const marker = this.markers.get(vId);
      marker.setLatLng(latLng);
      marker.setIcon(icon);
      marker.setPopupContent(popupHtml);
    } else {
      const marker = L.marker(latLng, { icon })
        .addTo(this.map)
        .bindPopup(popupHtml);
      this.markers.set(vId, marker);
    }
  }

  renderGeofences(geofences = []) {
    geofences.forEach(fence => {
      if (this.geofenceLayers.has(fence.id)) return;

      let layer = null;
      if (fence.fence_type === 'circle' && fence.center_latitude && fence.center_longitude) {
        layer = L.circle([fence.center_latitude, fence.center_longitude], {
          radius: fence.radius_meters || 1000,
          color: fence.color_hex || '#3B82F6',
          fillColor: fence.color_hex || '#3B82F6',
          fillOpacity: 0.15,
        }).addTo(this.map);
      } else if (fence.fence_type === 'polygon' && fence.coordinates && fence.coordinates.length > 2) {
        layer = L.polygon(fence.coordinates, {
          color: fence.color_hex || '#3B82F6',
          fillColor: fence.color_hex || '#3B82F6',
          fillOpacity: 0.15,
        }).addTo(this.map);
      }

      if (layer) {
        layer.bindPopup(`<b>${fence.name}</b><br>Type: ${fence.fence_type}`);
        this.geofenceLayers.set(fence.id, layer);
      }
    });
  }

  drawRouteHistory(waypoints = [], stops = []) {
    if (!this.map) return;

    // Clear previous elements
    if (this.historyPolyline) this.map.removeLayer(this.historyPolyline);
    if (this.startMarker) this.map.removeLayer(this.startMarker);
    if (this.endMarker) this.map.removeLayer(this.endMarker);
    this.stopMarkers.forEach(m => this.map.removeLayer(m));
    this.stopMarkers = [];

    const latLngs = waypoints.map(c => [c.latitude, c.longitude]);
    if (latLngs.length === 0) return;

    // Draw full trajectory
    this.historyPolyline = L.polyline(latLngs, {
      color: '#3B82F6',
      weight: 5,
      opacity: 0.85,
      lineCap: 'round',
    }).addTo(this.map);

    // Start point pin
    const startCoord = latLngs[0];
    const startIcon = L.divIcon({
      className: 'route-point-marker',
      html: '<div style="background: #10B981; width: 24px; height: 24px; border-radius: 50%; border: 3px solid #fff; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.5);"><i class="bi bi-play-fill text-white" style="font-size: 14px;"></i></div>',
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });
    this.startMarker = L.marker(startCoord, { icon: startIcon }).addTo(this.map).bindPopup('<b>Trip Start Point</b>');

    // End point pin
    if (latLngs.length > 1) {
      const endCoord = latLngs[latLngs.length - 1];
      const endIcon = L.divIcon({
        className: 'route-point-marker',
        html: '<div style="background: #EF4444; width: 24px; height: 24px; border-radius: 50%; border: 3px solid #fff; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 6px rgba(0,0,0,0.5);"><i class="bi bi-flag-fill text-white" style="font-size: 11px;"></i></div>',
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });
      this.endMarker = L.marker(endCoord, { icon: endIcon }).addTo(this.map).bindPopup('<b>Trip End Point</b>');
    }

    // Stop duration markers
    stops.forEach((s, idx) => {
      const stopIcon = L.divIcon({
        className: 'route-stop-marker',
        html: `<div style="background: #F59E0B; width: 22px; height: 22px; border-radius: 50%; border: 2px solid #fff; display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: bold; color: #000; box-shadow: 0 2px 5px rgba(0,0,0,0.4);">S${idx+1}</div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      });
      const stopMarker = L.marker([s.latitude, s.longitude], { icon: stopIcon })
        .addTo(this.map)
        .bindPopup(`<b>Stop #${idx+1}</b><br>Duration: ${Utils.formatDuration(s.duration_minutes)}<br>Arrived: ${Utils.formatDate(s.arrived_at)}`);
      this.stopMarkers.push(stopMarker);
    });

    this.map.fitBounds(this.historyPolyline.getBounds(), { padding: [50, 50] });
  }

  updatePlaybackPosition(lat, lng, heading = 0, speed = 0, timestamp = '') {
    if (!this.map || !lat || !lng) return;

    const latLng = [lat, lng];
    const icon = L.divIcon({
      className: 'playback-active-marker',
      html: `
        <div style="background: #3B82F6; width: 34px; height: 34px; border-radius: 50%; border: 3px solid #ffffff; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.6); transform: rotate(${heading}deg);">
          <i class="bi bi-truck-front-fill text-white fs-6"></i>
        </div>
      `,
      iconSize: [34, 34],
      iconAnchor: [17, 17],
    });

    if (this.playbackMarker) {
      this.playbackMarker.setLatLng(latLng);
      this.playbackMarker.setIcon(icon);
    } else {
      this.playbackMarker = L.marker(latLng, { icon }).addTo(this.map);
    }
  }
}
