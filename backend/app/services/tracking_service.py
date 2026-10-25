"""
GPS Tracking service — telemetry ingestion, live positions, route history.
Stop detection and offline truck flagging are also handled here.
"""
import math
from datetime import datetime, timezone, timedelta
from flask import current_app
from sqlalchemy import desc, asc
from app.extensions import db
from app.models.vehicle import Vehicle
from app.models.gps_device import GPSDevice
from app.models.gps_telemetry import GPSTelemetry
from app.models.trip import Trip, Stop
from app.models.alert import Alert
from app.utils.geo_utils import haversine_distance_km
from app.services.alert_service import AlertService
from app.services.geofence_service import GeofenceService


class TrackingService:
    """Processes real-time GPS packets, maintains live fleet state."""

    # ─── Telemetry Ingestion ───────────────────────────────────────────────────

    @staticmethod
    def process_telemetry(data: dict) -> dict:
        """
        Accept a raw GPS packet, resolve the vehicle, persist the point,
        update odometer, check alerts, and return a summary.

        Identification priority:
          1. vehicle_id (UUID)
          2. device_imei  (resolves via gps_devices table)
        """
        vehicle = TrackingService._resolve_vehicle(data)

        lat = float(data["latitude"])
        lng = float(data["longitude"])
        speed = float(data.get("speed_kmh") or data.get("speed") or 0.0)
        heading = float(data.get("heading") or 0.0)
        altitude = float(data["altitude"]) if data.get("altitude") is not None else None
        satellites = int(data.get("satellites") or 8)
        ignition = bool(data.get("ignition", True))
        battery_pct = float(data.get("battery_pct") or 100.0)
        fuel_level = float(data["fuel_level_pct"]) if data.get("fuel_level_pct") is not None else None

        recorded_at = TrackingService._parse_timestamp(
            data.get("timestamp") or data.get("recorded_at")
        )

        # ── Odometer accumulation ────────────────────────────────────────────
        last_point = (
            vehicle.telemetry
            .order_by(desc(GPSTelemetry.recorded_at))
            .first()
        )
        if last_point:
            delta_km = haversine_distance_km(
                last_point.latitude, last_point.longitude, lat, lng
            )
            # Sanity filter: > 5 m and < 50 km per sample interval
            if 0.005 < delta_km < 50.0:
                vehicle.current_odometer_km += delta_km

        # ── Persist telemetry point ──────────────────────────────────────────
        telemetry = GPSTelemetry(
            vehicle_id=vehicle.id,
            latitude=lat,
            longitude=lng,
            altitude=altitude,
            speed_kmh=speed,
            heading=heading,
            satellites=satellites,
            ignition=ignition,
            battery_pct=battery_pct,
            fuel_level_pct=fuel_level,
            odometer_km=vehicle.current_odometer_km,
            recorded_at=recorded_at,
        )
        db.session.add(telemetry)

        # ── Update vehicle status ────────────────────────────────────────────
        if speed > current_app.config.get("STOP_MAX_SPEED_KMH", 3.0):
            vehicle.status = "active"
        elif ignition:
            vehicle.status = "idle"
        else:
            vehicle.status = "offline"

        # ── Update GPS device last_seen ───────────────────────────────────────
        if vehicle.gps_device:
            vehicle.gps_device.last_seen_at = datetime.now(timezone.utc)

        # ── Alert evaluation ─────────────────────────────────────────────────
        alerts_generated = 0

        overspeed = AlertService.check_overspeed(vehicle, lat, lng, speed)
        if overspeed:
            alerts_generated += 1

        geo_alerts = GeofenceService.check_vehicle_geofences(vehicle, lat, lng, last_point)
        alerts_generated += len(geo_alerts)

        db.session.commit()

        return {
            "telemetry_id": telemetry.id,
            "vehicle_id": vehicle.id,
            "registration_number": vehicle.registration_number,
            "odometer_km": round(vehicle.current_odometer_km, 1),
            "alerts_generated": alerts_generated,
        }

    # ─── Live Fleet Snapshot ───────────────────────────────────────────────────

    @staticmethod
    def get_live_fleet_positions(organization_id: str | None = None) -> list:
        """Return the most-recent GPS point for every vehicle in the fleet."""
        query = Vehicle.query
        if organization_id:
            query = query.filter_by(organization_id=organization_id)

        vehicles = query.all()
        fleet_data = []

        for v in vehicles:
            latest = (
                v.telemetry
                .order_by(desc(GPSTelemetry.recorded_at))
                .first()
            )
            fleet_data.append({
                "vehicle_id": v.id,
                "registration_number": v.registration_number,
                "make_model": f"{v.make} {v.model}",
                "status": v.status,
                "driver_name": v.assigned_driver.full_name if v.assigned_driver else "Unassigned",
                "driver_id": v.assigned_driver_id,
                "latitude": latest.latitude if latest else None,
                "longitude": latest.longitude if latest else None,
                "speed_kmh": latest.speed_kmh if latest else 0.0,
                "heading": latest.heading if latest else 0.0,
                "ignition": latest.ignition if latest else False,
                "battery_pct": latest.battery_pct if latest else None,
                "fuel_level_pct": latest.fuel_level_pct if latest else None,
                "odometer_km": round(v.current_odometer_km, 1),
                "last_updated": latest.recorded_at.isoformat() if latest else None,
            })

        return fleet_data

    @staticmethod
    def get_live_truck_position(truck_id: str) -> dict:
        """Return the live snapshot for a single truck."""
        vehicle = Vehicle.query.get(truck_id)
        if not vehicle:
            raise ValueError("Truck not found")

        latest = (
            vehicle.telemetry
            .order_by(desc(GPSTelemetry.recorded_at))
            .first()
        )
        return {
            "vehicle_id": vehicle.id,
            "registration_number": vehicle.registration_number,
            "make_model": f"{vehicle.make} {vehicle.model}",
            "status": vehicle.status,
            "driver_name": vehicle.assigned_driver.full_name if vehicle.assigned_driver else "Unassigned",
            "latitude": latest.latitude if latest else None,
            "longitude": latest.longitude if latest else None,
            "speed_kmh": latest.speed_kmh if latest else 0.0,
            "heading": latest.heading if latest else 0.0,
            "ignition": latest.ignition if latest else False,
            "battery_pct": latest.battery_pct if latest else None,
            "fuel_level_pct": latest.fuel_level_pct if latest else None,
            "odometer_km": round(vehicle.current_odometer_km, 1),
            "last_updated": latest.recorded_at.isoformat() if latest else None,
        }

    # ─── History / Playback ────────────────────────────────────────────────────

    @staticmethod
    def get_vehicle_gps_history(
        vehicle_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list:
        """
        Return historical telemetry points for a vehicle, ordered by time.
        Optional start_time / end_time window filter.
        """
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            raise ValueError("Truck not found")

        q = vehicle.telemetry
        if start_time:
            q = q.filter(GPSTelemetry.recorded_at >= start_time)
        if end_time:
            q = q.filter(GPSTelemetry.recorded_at <= end_time)

        points = q.order_by(asc(GPSTelemetry.recorded_at)).limit(limit).all()
        return [p.to_dict() for p in points]

    # ─── Offline Truck Detection ───────────────────────────────────────────────

    @staticmethod
    def flag_offline_trucks() -> int:
        """
        Mark vehicles offline if their last telemetry is older than
        OFFLINE_TRUCK_MINUTES. Fires a truck_offline alert once per vehicle.
        Returns count of newly flagged trucks.
        """
        offline_threshold = current_app.config.get("OFFLINE_TRUCK_MINUTES", 10)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=offline_threshold)

        vehicles = Vehicle.query.filter(Vehicle.status != "maintenance").all()
        flagged = 0

        for v in vehicles:
            latest = (
                v.telemetry
                .order_by(desc(GPSTelemetry.recorded_at))
                .first()
            )
            if latest and latest.recorded_at < cutoff and v.status != "offline":
                v.status = "offline"
                # Only raise alert if not already an unacknowledged truck_offline for this vehicle
                existing = Alert.query.filter_by(
                    vehicle_id=v.id,
                    alert_type="truck_offline",
                    is_acknowledged=False,
                ).first()
                if not existing:
                    alert = Alert(
                        organization_id=v.organization_id,
                        vehicle_id=v.id,
                        alert_type="truck_offline",
                        severity="warning",
                        message=(
                            f"Truck {v.registration_number} has not reported GPS "
                            f"data for >{offline_threshold} minutes"
                        ),
                    )
                    db.session.add(alert)
                flagged += 1

        db.session.commit()
        return flagged

    # ─── Stop Detection ────────────────────────────────────────────────────────

    @staticmethod
    def detect_stops(trip_id: str) -> list[dict]:
        """
        Analyse telemetry for a trip and detect stationary segments that last
        >= STOP_MIN_SECONDS.  Saves Stop records to the database.
        Returns a list of stop dicts.
        """
        trip = Trip.query.get(trip_id)
        if not trip:
            raise ValueError("Trip not found")

        stop_max_speed = current_app.config.get("STOP_MAX_SPEED_KMH", 3.0)
        stop_min_seconds = current_app.config.get("STOP_MIN_SECONDS", 120)

        q = GPSTelemetry.query.filter(
            GPSTelemetry.vehicle_id == trip.vehicle_id,
            GPSTelemetry.recorded_at >= trip.start_time,
        )
        if trip.end_time:
            q = q.filter(GPSTelemetry.recorded_at <= trip.end_time)
        points = q.order_by(asc(GPSTelemetry.recorded_at)).all()

        stops = []
        stop_start: datetime | None = None
        stop_lat: float | None = None
        stop_lng: float | None = None

        for pt in points:
            if pt.speed_kmh <= stop_max_speed:
                if stop_start is None:
                    stop_start = pt.recorded_at
                    stop_lat = pt.latitude
                    stop_lng = pt.longitude
            else:
                if stop_start is not None:
                    duration_sec = (pt.recorded_at - stop_start).total_seconds()
                    if duration_sec >= stop_min_seconds:
                        stop_rec = Stop(
                            trip_id=trip.id,
                            vehicle_id=trip.vehicle_id,
                            latitude=stop_lat,
                            longitude=stop_lng,
                            arrived_at=stop_start,
                            departed_at=pt.recorded_at,
                            duration_minutes=round(duration_sec / 60, 1),
                        )
                        db.session.add(stop_rec)
                        stops.append(stop_rec.to_dict())
                    stop_start = None

        db.session.commit()
        return stops

    # ─── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _resolve_vehicle(data: dict) -> Vehicle:
        vehicle_id = data.get("vehicle_id")
        device_imei = data.get("device_imei")

        vehicle = None
        if vehicle_id:
            vehicle = Vehicle.query.get(vehicle_id)
        elif device_imei:
            device = GPSDevice.query.filter_by(imei=str(device_imei)).first()
            if device:
                vehicle = device.vehicle
        if not vehicle:
            raise ValueError(
                "Vehicle not found. Provide a valid vehicle_id or device_imei."
            )
        return vehicle

    @staticmethod
    def _parse_timestamp(value) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)
