"""
Alert service — safety threshold evaluation and incident management.
"""
from datetime import datetime, timezone, timedelta
from flask import current_app
from app.extensions import db
from app.models.alert import Alert
from app.models.vehicle import Vehicle


class AlertService:

    @staticmethod
    def check_overspeed(
        vehicle: Vehicle, lat: float, lng: float, speed_kmh: float
    ) -> Alert | None:
        """
        Create an overspeed alert if the vehicle exceeds its speed limit.
        Uses vehicle-specific limit if set, otherwise falls back to org-level config.
        """
        limit = vehicle.speed_limit_kmh or current_app.config.get("SPEED_LIMIT_KMH", 80.0)
        if speed_kmh <= limit:
            return None

        # Deduplicate: don't spam — skip if an unacknowledged overspeed alert
        # was raised for this vehicle within the last 5 minutes
        cooldown = timedelta(minutes=5)
        recent_cutoff = datetime.now(timezone.utc) - cooldown
        existing = Alert.query.filter(
            Alert.vehicle_id == vehicle.id,
            Alert.alert_type == "overspeed",
            Alert.is_acknowledged == False,
            Alert.created_at >= recent_cutoff,
        ).first()
        if existing:
            return None

        severity = "critical" if speed_kmh > (limit + 20) else "warning"
        alert = Alert(
            organization_id=vehicle.organization_id,
            vehicle_id=vehicle.id,
            alert_type="overspeed",
            severity=severity,
            message=(
                f"Truck {vehicle.registration_number} exceeded "
                f"{limit:.0f} km/h limit (recorded {speed_kmh:.1f} km/h)"
            ),
            latitude=lat,
            longitude=lng,
            speed_kmh=speed_kmh,
        )
        db.session.add(alert)
        return alert

    @staticmethod
    def acknowledge_alert(alert_id: str, user_id: str) -> Alert:
        """Acknowledge / dismiss an alert."""
        alert = Alert.query.get(alert_id)
        if not alert:
            raise ValueError("Alert not found")
        if alert.is_acknowledged:
            raise ValueError("Alert is already acknowledged")

        alert.is_acknowledged = True
        alert.acknowledged_by = user_id
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.session.commit()
        return alert

    @staticmethod
    def create_alert(
        vehicle: Vehicle,
        alert_type: str,
        message: str,
        severity: str = "warning",
        lat: float | None = None,
        lng: float | None = None,
        speed_kmh: float | None = None,
        geofence_id: str | None = None,
        trip_id: str | None = None,
    ) -> Alert:
        """Generic alert factory used by other services."""
        alert = Alert(
            organization_id=vehicle.organization_id,
            vehicle_id=vehicle.id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            latitude=lat,
            longitude=lng,
            speed_kmh=speed_kmh,
            geofence_id=geofence_id,
            trip_id=trip_id,
        )
        db.session.add(alert)
        return alert
