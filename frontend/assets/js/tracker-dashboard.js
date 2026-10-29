/**
 * TRANSPORT GPS TRACKING - LUXURY TRACKER DASHBOARD CONTROLLER
 * Handles interactive packages, Leaflet map route visualization, driver actions,
 * real-time search filtering, and custom SVG visual fallbacks.
 */

(function () {
  'use strict';

  // Package Data Repository (matching the mockup exactly)
  const PACKAGES_DATA = [
    {
      id: 'KG3200L3122324GF',
      trackingNumber: 'KG3200L3122324GF',
      status: 'In Transit',
      statusType: 'transit',
      departure: '22.08.21 16:40 PM',
      arrival: '24.08.21 12:30 PM',
      customer: 'Ella Doer',
      price: '1334 $',
      description: 'Clothes',
      weight: '1,2 kg',
      driver: {
        name: 'John Green',
        role: 'Driver',
        phone: '+1 (555) 234-8901',
        avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&q=80'
      },
      route: {
        from: 'Moraga Ave',
        to: 'The Walt Disney Family Museum',
        center: [37.7982, -122.4595],
        startCoords: [37.7940, -122.4638],
        endCoords: [37.8008, -122.4582],
        path: [
          [37.7940, -122.4638],
          [37.7952, -122.4628],
          [37.7963, -122.4619],
          [37.7975, -122.4608],
          [37.7989, -122.4595],
          [37.8001, -122.4587],
          [37.8008, -122.4582]
        ]
      }
    },
    {
      id: 'PRS0574L1901200CH',
      trackingNumber: 'PRS0574L1901200CH',
      routeTitle: 'Paris → Barcelona',
      status: 'In Transit',
      statusType: 'transit',
      departure: '23.08.21 09:15 AM',
      arrival: '25.08.21 18:00 PM',
      customer: 'Lucia Moreau',
      price: '890 $',
      description: 'Electronics',
      weight: '3,4 kg',
      driver: {
        name: 'Marc Dubois',
        role: 'Driver',
        phone: '+33 6 12 34 56 78',
        avatar: 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?auto=format&fit=crop&w=120&q=80'
      },
      iconClass: 'badge-bg-purple',
      iconSvg: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 15s3-3 8-3 8 3 8 3M4 9s3-3 8-3 8 3 8 3"/></svg>`,
      route: {
        from: 'Paris Hub',
        to: 'Barcelona Port',
        center: [37.7982, -122.4595],
        startCoords: [37.7935, -122.4650],
        endCoords: [37.8012, -122.4575],
        path: [
          [37.7935, -122.4650],
          [37.7950, -122.4630],
          [37.7970, -122.4610],
          [37.7990, -122.4590],
          [37.8012, -122.4575]
        ]
      }
    },
    {
      id: 'VNE8365L1465901YT',
      trackingNumber: 'VNE8365L1465901YT',
      routeTitle: 'Vancouver → New York',
      status: 'In Transit',
      statusType: 'transit',
      departure: '21.08.21 14:00 PM',
      arrival: '26.08.21 11:45 AM',
      customer: 'Alex Carter',
      price: '2150 $',
      description: 'Luxury Goods',
      weight: '5,8 kg',
      driver: {
        name: 'David Hayes',
        role: 'Driver',
        phone: '+1 (555) 890-1234',
        avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=120&q=80'
      },
      iconClass: 'badge-bg-blue',
      iconSvg: `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="7" r="2.5"/><circle cx="7" cy="16" r="2.5"/><circle cx="17" cy="16" r="2.5"/><circle cx="12" cy="13" r="1.5"/></svg>`,
      route: {
        from: 'Vancouver Terminal',
        to: 'New York JFK',
        center: [37.7982, -122.4595],
        startCoords: [37.7945, -122.4625],
        endCoords: [37.8005, -122.4580],
        path: [
          [37.7945, -122.4625],
          [37.7960, -122.4610],
          [37.7980, -122.4595],
          [37.8005, -122.4580]
        ]
      }
    },
    {
      id: 'ARM9738L1475824MT',
      trackingNumber: 'ARM9738L1475824MT',
      routeTitle: 'Amsterdam → Dresden',
      status: 'In Transit',
      statusType: 'transit',
      departure: '24.08.21 08:30 AM',
      arrival: '25.08.21 15:20 PM',
      customer: 'Helena Schmidt',
      price: '740 $',
      description: 'Medical Tech',
      weight: '0,9 kg',
      driver: {
        name: 'Klaus Weber',
        role: 'Driver',
        phone: '+49 171 2345678',
        avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=120&q=80'
      },
      iconClass: 'badge-bg-green',
      iconSvg: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="4" x2="12" y2="20"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="6.34" y1="6.34" x2="17.66" y2="17.66"/><line x1="6.34" y1="17.66" x2="17.66" y2="6.34"/></svg>`,
      route: {
        from: 'Amsterdam Logistics',
        to: 'Dresden Depot',
        center: [37.7982, -122.4595],
        startCoords: [37.7940, -122.4640],
        endCoords: [37.8008, -122.4582],
        path: [
          [37.7940, -122.4640],
          [37.7960, -122.4620],
          [37.7985, -122.4600],
          [37.8008, -122.4582]
        ]
      }
    },
    {
      id: 'WRS9476L8466747AR',
      trackingNumber: 'WRS9476L8466747AR',
      routeTitle: 'Warsaw → Kyiv',
      status: 'Packed',
      statusType: 'packed',
      departure: '25.08.21 10:00 AM',
      arrival: '27.08.21 19:00 PM',
      customer: 'Dmytro Kovalenko',
      price: '420 $',
      description: 'Machinery Parts',
      weight: '8,4 kg',
      driver: {
        name: 'Marek Wisniewski',
        role: 'Driver',
        phone: '+48 22 123 4567',
        avatar: 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?auto=format&fit=crop&w=120&q=80'
      },
      iconClass: 'badge-bg-amber',
      iconSvg: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/></svg>`,
      route: {
        from: 'Warsaw Central',
        to: 'Kyiv Terminal',
        center: [37.7982, -122.4595],
        startCoords: [37.7942, -122.4635],
        endCoords: [37.8008, -122.4582],
        path: [
          [37.7942, -122.4635],
          [37.7955, -122.4625],
          [37.7975, -122.4605],
          [37.8008, -122.4582]
        ]
      }
    }
  ];

  let currentPackage = PACKAGES_DATA[0];
  let leafletMap = null;
  let mapPolyline = null;
  let originMarker = null;
  let destinationMarker = null;
  let floatingTooltipMarker = null;

  // DOM Elements
  const elTrackingNum = document.getElementById('active-tracking-num');
  const elStatusBadge = document.getElementById('active-status-badge');
  const elDeparture = document.getElementById('active-departure-time');
  const elArrival = document.getElementById('active-arrival-time');
  const elCustomer = document.getElementById('active-customer-val');
  const elPrice = document.getElementById('active-price-val');
  const elDesc = document.getElementById('active-desc-val');
  const elWeight = document.getElementById('active-weight-val');
  const elDriverName = document.getElementById('active-driver-name');
  const elDriverAvatar = document.getElementById('active-driver-avatar');
  const elShipmentsList = document.getElementById('shipments-list-container');
  const elSearchInput = document.getElementById('dashboard-search-input');
  const elNewPackageInput = document.getElementById('new-package-input');
  const elNewPackageForm = document.getElementById('new-package-form');
  const elFloatingCardCode = document.getElementById('map-floating-code');
  const elFloatingCardStatus = document.getElementById('map-floating-status');
  const elToast = document.getElementById('tracker-toast-notice');
  const elToastMsg = document.getElementById('tracker-toast-msg');

  // Initialization
  document.addEventListener('DOMContentLoaded', () => {
    checkLoggedUser();
    renderShipmentsList(PACKAGES_DATA.slice(1));
    updateActivePackageCard(currentPackage);
    initMap();
    setupEventHandlers();
  });

  /**
   * Check if user is logged into the system, update header without blocking viewer
   */
  function checkLoggedUser() {
    try {
      const rawUser = localStorage.getItem('tgt_user_data');
      if (rawUser) {
        const u = JSON.parse(rawUser);
        const nameEl = document.querySelector('.user-name-text');
        if (nameEl && (u.full_name || u.first_name)) {
          nameEl.textContent = u.full_name || `${u.first_name} ${u.last_name || ''}`.trim();
        }
      }
    } catch (e) {
      console.warn('User profile parse:', e);
    }
  }

  /**
   * Populate Active Shipment Card
   */
  function updateActivePackageCard(pkg) {
    currentPackage = pkg;

    if (elTrackingNum) elTrackingNum.textContent = pkg.trackingNumber;
    if (elFloatingCardCode) elFloatingCardCode.textContent = pkg.trackingNumber;

    const dotClass = pkg.statusType === 'packed' ? 'packed' : (pkg.statusType === 'delivered' ? 'delivered' : 'transit');
    const badgeHtml = `<span class="status-dot ${dotClass}"></span>${pkg.status}`;

    if (elStatusBadge) elStatusBadge.innerHTML = badgeHtml;
    if (elFloatingCardStatus) elFloatingCardStatus.innerHTML = badgeHtml;

    if (elDeparture) elDeparture.textContent = pkg.departure;
    if (elArrival) elArrival.textContent = pkg.arrival;
    if (elCustomer) elCustomer.textContent = pkg.customer;
    if (elPrice) elPrice.textContent = pkg.price;
    if (elDesc) elDesc.textContent = pkg.description;
    if (elWeight) elWeight.textContent = pkg.weight;

    if (elDriverName && pkg.driver) elDriverName.textContent = pkg.driver.name;
    if (elDriverAvatar && pkg.driver) {
      elDriverAvatar.src = pkg.driver.avatar;
      elDriverAvatar.alt = pkg.driver.name;
    }

    // Refresh Map Path & Tooltip
    updateMapForPackage(pkg);
  }

  /**
   * Render package history list items
   */
  function renderShipmentsList(list) {
    if (!elShipmentsList) return;
    elShipmentsList.innerHTML = '';

    list.forEach(item => {
      const row = document.createElement('div');
      row.className = `shipment-row-item ${item.id === currentPackage.id ? 'selected' : ''}`;
      row.dataset.id = item.id;

      const dotClass = item.statusType === 'packed' ? 'packed' : 'transit';

      row.innerHTML = `
        <div class="shipment-left-info">
          <div class="shipment-icon-badge ${item.iconClass || 'badge-bg-purple'}">
            ${item.iconSvg || `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s3-3 8-3 8 3 8 3"/></svg>`}
          </div>
          <div>
            <span class="shipment-code-text">${item.trackingNumber}</span>
            <span class="shipment-route-text">${item.routeTitle || item.route?.from + ' → ' + item.route?.to}</span>
          </div>
        </div>
        <div class="shipment-status-pill">
          <span class="status-dot ${dotClass}"></span>
          <span>${item.status}</span>
        </div>
      `;

      row.addEventListener('click', () => {
        document.querySelectorAll('.shipment-row-item').forEach(r => r.classList.remove('selected'));
        row.classList.add('selected');
        updateActivePackageCard(item);
      });

      elShipmentsList.appendChild(row);
    });
  }

  /**
   * Initialize Leaflet Interactive Map
   */
  function initMap() {
    const mapContainer = document.getElementById('tracker-map-view');
    if (!mapContainer) return;

    const center = currentPackage.route?.center || [37.7982, -122.4595];

    if (typeof L !== 'undefined') {
      try {
        leafletMap = L.map('tracker-map-view', {
          zoomControl: false,
          attributionControl: false
        }).setView(center, 16);

        // CartoDB Positron - ultra-clean minimalist light theme tiles
        const tileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
          subdomains: 'abcd',
          maxZoom: 19
        }).addTo(leafletMap);

        // When Leaflet tile layer loads, seamlessly adapt the fallback vector layer
        tileLayer.on('load', () => {
          const fallback = document.querySelector('.map-canvas-layer');
          if (fallback) {
            fallback.style.opacity = '0';
            fallback.style.transition = 'opacity 0.5s ease';
          }
        });
        const pinIcon = L.divIcon({
          className: 'custom-destination-marker',
          html: `
            <svg class="map-destination-pin" viewBox="0 0 24 30" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 0C5.37258 0 0 5.37258 0 12C0 19.5 12 30 12 30C12 30 24 19.5 24 12C24 5.37258 18.6274 0 12 0Z" fill="#121316"/>
              <circle cx="12" cy="11" r="4.5" fill="#FFFFFF"/>
            </svg>
          `,
          iconSize: [26, 32],
          iconAnchor: [13, 32]
        });

        // Origin Radar Beacon Marker
        const radarIcon = L.divIcon({
          className: 'custom-radar-marker',
          html: `
            <div class="map-radar-marker">
              <div class="radar-halo-pulse"></div>
              <div class="radar-center-dot"></div>
            </div>
          `,
          iconSize: [48, 48],
          iconAnchor: [24, 24]
        });

        originMarker = L.marker(currentPackage.route.startCoords, { icon: radarIcon }).addTo(leafletMap);
        destinationMarker = L.marker(currentPackage.route.endCoords, { icon: pinIcon }).addTo(leafletMap);

        // Sleek route polyline
        mapPolyline = L.polyline(currentPackage.route.path, {
          color: '#121316',
          weight: 4.5,
          opacity: 0.95,
          lineCap: 'round',
          lineJoin: 'round'
        }).addTo(leafletMap);

        // Setup Zoom Controls
        const btnZoomIn = document.getElementById('map-btn-zoom-in');
        const btnZoomOut = document.getElementById('map-btn-zoom-out');

        if (btnZoomIn) {
          btnZoomIn.addEventListener('click', () => leafletMap.zoomIn());
        }
        if (btnZoomOut) {
          btnZoomOut.addEventListener('click', () => leafletMap.zoomOut());
        }
      } catch (err) {
        console.warn('Leaflet tile layer fallback active:', err);
      }
    }
  }

  /**
   * Update map coordinates and route polyline when package changes
   */
  function updateMapForPackage(pkg) {
    if (!leafletMap || !pkg.route) return;

    try {
      if (originMarker) originMarker.setLatLng(pkg.route.startCoords);
      if (destinationMarker) destinationMarker.setLatLng(pkg.route.endCoords);
      if (mapPolyline) mapPolyline.setLatLngs(pkg.route.path);

      leafletMap.panTo(pkg.route.center, { animate: true, duration: 0.8 });
    } catch (e) {
      console.warn('Map update:', e);
    }
  }

  /**
   * Event Listeners (Form submission, Search, Driver Actions, View Toggles)
   */
  function setupEventHandlers() {
    // Add New Package Form Submission
    if (elNewPackageForm) {
      elNewPackageForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const code = (elNewPackageInput?.value || '').trim().toUpperCase();
        if (!code) {
          showToast('Please enter a valid tracking number');
          return;
        }

        const newPkg = {
          id: code,
          trackingNumber: code,
          routeTitle: 'Regional Hub → Destination Depot',
          status: 'In Transit',
          statusType: 'transit',
          departure: 'Today ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          arrival: 'Estimated in 2 Days',
          customer: 'Ella Doer',
          price: '650 $',
          description: 'Priority Parcel',
          weight: '1,5 kg',
          driver: {
            name: 'John Green',
            role: 'Driver',
            phone: '+1 (555) 234-8901',
            avatar: 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=120&q=80'
          },
          iconClass: 'badge-bg-blue',
          iconSvg: `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="7" r="2.5"/><circle cx="7" cy="16" r="2.5"/><circle cx="17" cy="16" r="2.5"/><circle cx="12" cy="13" r="1.5"/></svg>`,
          route: currentPackage.route
        };

        PACKAGES_DATA.unshift(newPkg);
        elNewPackageInput.value = '';
        renderShipmentsList(PACKAGES_DATA.slice(1));
        updateActivePackageCard(newPkg);
        showToast(`Package ${code} registered successfully!`);
      });
    }

    // Live Search Filter
    if (elSearchInput) {
      elSearchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        const filtered = PACKAGES_DATA.slice(1).filter(p =>
          p.trackingNumber.toLowerCase().includes(query) ||
          (p.routeTitle && p.routeTitle.toLowerCase().includes(query)) ||
          p.customer.toLowerCase().includes(query)
        );
        renderShipmentsList(filtered);
      });
    }

    // Driver Action Buttons
    const btnCall = document.getElementById('driver-action-call');
    const btnMsg = document.getElementById('driver-action-message');

    if (btnCall) {
      btnCall.addEventListener('click', () => {
        showToast(`Calling driver ${currentPackage.driver?.name || 'Driver'} (${currentPackage.driver?.phone || '+1 555-0192'})...`);
      });
    }

    if (btnMsg) {
      btnMsg.addEventListener('click', () => {
        showToast(`Opening dispatch messenger with ${currentPackage.driver?.name || 'Driver'}...`);
      });
    }

    // Notification Bell Click
    const bellBtn = document.querySelector('.bell-btn');
    if (bellBtn) {
      bellBtn.addEventListener('click', () => {
        showToast('2 In-Transit notifications: Cargo arriving on schedule.');
      });
    }

    // View Mode Toggle (Device Canvas vs Fullscreen App)
    const btnModeDevice = document.getElementById('btn-mode-device');
    const btnModeFull = document.getElementById('btn-mode-full');

    if (btnModeDevice && btnModeFull) {
      btnModeDevice.addEventListener('click', (e) => {
        e.preventDefault();
        document.body.classList.remove('fullscreen-mode');
        btnModeDevice.classList.add('active');
        btnModeFull.classList.remove('active');
        if (leafletMap) leafletMap.invalidateSize();
      });

      btnModeFull.addEventListener('click', (e) => {
        e.preventDefault();
        document.body.classList.add('fullscreen-mode');
        btnModeFull.classList.add('active');
        btnModeDevice.classList.remove('active');
        if (leafletMap) leafletMap.invalidateSize();
      });
    }
  }

  /**
   * Sleek Action Feedback Toast
   */
  function showToast(message) {
    if (!elToast || !elToastMsg) return;
    elToastMsg.textContent = message;
    elToast.classList.add('show');
    clearTimeout(window.__toastTimeout);
    window.__toastTimeout = setTimeout(() => {
      elToast.classList.remove('show');
    }, 3400);
  }

})();
