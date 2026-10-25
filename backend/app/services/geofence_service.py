"""
Geofence service — spatial containment checks and entry/exit event generation.
"""
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.extensions import db
from app.models.geofence import Geofence
from app.models.alert import Alert
from app.models.vehicle import Vehicle
from app.models.gps_telemetry import GPSTelemetry
from app.utils.geo_utils import is_point_in_circle, is_point_in_polygon


class GeofenceService:

    @staticmethod
    def is_inside(lat: float, lng: float, fence: Geofence) -> bool:
        """Check whether coordinate (lat, lng) is inside the given geofence."""
        if fence.fence_type == "circle":
            if None in (fence.center_latitude, fence.center_longitude, fence.radius_meters):
                return False
            return is_point_in_circle(
                lat, lng,
                fence.center_latitude,
                fence.center_longitude,
                fence.radius_meters,
            )
        if fence.fence_type == "polygon":
            coords = fence.coordinates
            if not coords or len(coords) < 3:
                return False
            return is_point_in_polygon(lat, lng, coords)
        return False

    @classmethod
    def check_vehicle_geofences(
        cls,
        vehicle: Vehicle,
        curr_lat: float,
        curr_lng: float,
        prev_point: GPSTelemetry | None,
    ) -> list[Alert]:
        """
        Evaluate active geofences for the vehicle's organisation.
        Fires entry or exit alerts on transition only (not on every point).
        Respects cooldown window to prevent alert storms.
        """
        if vehicle.organization_id:
            fences = (
                Geofence.query
                .filter_by(organization_id=vehicle.organization_id, is_active=True)
                .all()
            )
        else:
            fences = Geofence.query.filter_by(is_active=True).all()

        cooldown_mins = current_app.config.get("GEOFENCE_ALERT_COOLDOWN_MINUTES", 5)
        cooldown_cutoff = datetime.now(timezone.utc) - timedelta(minutes=cooldown_mins)
        alerts: list[Alert] = []

        for fence in fences:
            curr_inside = cls.is_inside(curr_lat, curr_lng, fence)

            if prev_point is None:
                # First ever point — can't detect transition
                continue

            prev_inside = cls.is_inside(prev_point.latitude, prev_point.longitude, fence)

            # Entry transition
            if not prev_inside and curr_inside and fence.alert_on_entry:
                if not cls._recent_alert_exists(vehicle.id, fence.id, "geofence_entry", cooldown_cutoff):
                    alert = Alert(
                        organization_id=vehicle.organization_id,
                        vehicle_id=vehicle.id,
                        geofence_id=fence.id,
                        alert_type="geofence_entry",
                        severity="info",
                        message=f"Truck {vehicle.registration_number} entered geofence: {fence.name}",
                        latitude=curr_lat,
                        longitude=curr_lng,
                    )
                    db.session.add(alert)
                    alerts.append(alert)

            # Exit transition
            elif prev_inside and not curr_inside and fence.alert_on_exit:
                if not cls._recent_alert_exists(vehicle.id, fence.id, "geofence_exit", cooldown_cutoff):
                    alert = Alert(
                        organization_id=vehicle.organization_id,
                        vehicle_id=vehicle.id,
                        geofence_id=fence.id,
                        alert_type="geofence_exit",
                        severity="warning",
                        message=f"Truck {vehicle.registration_number} exited geofence: {fence.name}",
                        latitude=curr_lat,
                        longitude=curr_lng,
                    )
                    db.session.add(alert)
                    alerts.append(alert)

        return alerts

    @staticmethod
    def _recent_alert_exists(
        vehicle_id: str, geofence_id: str, alert_type: str, cutoff: datetime
    ) -> bool:
        return Alert.query.filter(
            Alert.vehicle_id == vehicle_id,
            Alert.geofence_id == geofence_id,
            Alert.alert_type == alert_type,
            Alert.created_at >= cutoff,
        ).first() is not None
