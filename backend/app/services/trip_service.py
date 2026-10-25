"""
Trip service — start, complete, cancel, and event recording.
"""
from datetime import datetime, timezone
from app.extensions import db
from app.models.trip import Trip, TripEvent, TRIP_EVENT_TYPES
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.utils.geo_utils import haversine_distance_km


class TripService:

    @staticmethod
    def start_trip(
        vehicle_id: str,
        start_lat: float,
        start_lng: float,
        driver_id: str | None = None,
        organization_id: str | None = None,
        notes: str | None = None,
        load_status: str | None = "empty",
    ) -> Trip:
        """
        Begin a new trip for a vehicle.
        Raises ValueError if the vehicle already has an in-progress trip.
        """
        vehicle = Vehicle.query.get(vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found")

        # Guard: only one active trip per vehicle
        active = Trip.query.filter_by(vehicle_id=vehicle_id, status="in_progress").first()
        if active:
            raise ValueError(
                f"Vehicle already has an in-progress trip (id={active.id}). "
                "Complete or cancel it first."
            )

        resolved_driver_id = driver_id or vehicle.assigned_driver_id
        trip = Trip(
            organization_id=organization_id or vehicle.organization_id,
            vehicle_id=vehicle_id,
            driver_id=resolved_driver_id,
            status="in_progress",
            load_status=load_status or "empty",
            start_time=datetime.now(timezone.utc),
            start_latitude=start_lat,
            start_longitude=start_lng,
            notes=notes,
        )
        db.session.add(trip)
        db.session.flush()

        # Record trip_start event
        TripService._add_event(
            trip, "trip_start", start_lat, start_lng,
            description=f"Trip started at ({start_lat:.5f}, {start_lng:.5f})"
        )
        db.session.commit()
        return trip

    @staticmethod
    def complete_trip(
        trip_id: str,
        end_lat: float,
        end_lng: float,
        notes: str | None = None,
    ) -> Trip:
        """Finalise a trip: compute duration, distance, avg speed, detect stops."""
        trip = TripService._get_active_trip(trip_id)
        now = datetime.now(timezone.utc)

        trip.end_time = now
        trip.end_latitude = end_lat
        trip.end_longitude = end_lng
        trip.status = "completed"

        if notes:
            trip.notes = notes

        # Duration
        delta = now - (
            trip.start_time.replace(tzinfo=timezone.utc)
            if trip.start_time.tzinfo is None else trip.start_time
        )
        trip.duration_minutes = round(delta.total_seconds() / 60, 1)

        # Compute cumulative distance from telemetry
        from app.models.gps_telemetry import GPSTelemetry
        from sqlalchemy import asc
        points = (
            GPSTelemetry.query
            .filter_by(vehicle_id=trip.vehicle_id)
            .filter(GPSTelemetry.recorded_at >= trip.start_time)
            .filter(GPSTelemetry.recorded_at <= now)
            .order_by(asc(GPSTelemetry.recorded_at))
            .all()
        )
        total_km = 0.0
        speeds = []
        max_speed = 0.0
        for i in range(1, len(points)):
            seg_km = haversine_distance_km(
                points[i - 1].latitude, points[i - 1].longitude,
                points[i].latitude, points[i].longitude,
            )
            if 0 < seg_km < 50:
                total_km += seg_km
            if points[i].speed_kmh:
                speeds.append(points[i].speed_kmh)
                if points[i].speed_kmh > max_speed:
                    max_speed = points[i].speed_kmh

        trip.distance_km = round(total_km, 2)
        trip.max_speed_kmh = round(max_speed, 1)
        trip.avg_speed_kmh = round(sum(speeds) / len(speeds), 1) if speeds else 0.0

        # Record event
        TripService._add_event(
            trip, "trip_end", end_lat, end_lng,
            description=f"Trip completed. {trip.distance_km} km in {trip.duration_minutes} mins."
        )

        db.session.commit()
        return trip

    @staticmethod
    def cancel_trip(trip_id: str, reason: str | None = None) -> Trip:
        """Cancel an in-progress trip."""
        trip = TripService._get_active_trip(trip_id)
        trip.status = "cancelled"
        trip.notes = reason or trip.notes
        TripService._add_event(
            trip, "trip_cancel", None, None,
            description=f"Trip cancelled. Reason: {reason or 'unspecified'}"
        )
        db.session.commit()
        return trip

    @staticmethod
    def add_trip_event(
        trip_id: str,
        event_type: str,
        lat: float | None = None,
        lng: float | None = None,
        speed_kmh: float | None = None,
        heading: float | None = None,
        description: str | None = None,
        occurred_at: datetime | None = None,
    ) -> TripEvent:
        """Append a discrete event (overspeed, harsh-brake, etc.) to a trip."""
        trip = Trip.query.get(trip_id)
        if not trip:
            raise ValueError("Trip not found")
        if event_type not in TRIP_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type '{event_type}'. "
                f"Must be one of: {', '.join(TRIP_EVENT_TYPES)}"
            )

        event = TripEvent(
            trip_id=trip.id,
            vehicle_id=trip.vehicle_id,
            event_type=event_type,
            latitude=lat,
            longitude=lng,
            speed_kmh=speed_kmh,
            heading=heading,
            description=description,
            occurred_at=occurred_at or datetime.now(timezone.utc),
        )
        db.session.add(event)
        db.session.commit()
        return event

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _get_active_trip(trip_id: str) -> Trip:
        trip = Trip.query.get(trip_id)
        if not trip:
            raise ValueError("Trip not found")
        if trip.status != "in_progress":
            raise ValueError(f"Trip is already '{trip.status}', cannot modify.")
        return trip

    @staticmethod
    def _add_event(
        trip: Trip,
        event_type: str,
        lat,
        lng,
        speed_kmh=None,
        description=None,
    ):
        event = TripEvent(
            trip_id=trip.id,
            vehicle_id=trip.vehicle_id,
            event_type=event_type,
            latitude=lat,
            longitude=lng,
            speed_kmh=speed_kmh,
            description=description,
            occurred_at=datetime.now(timezone.utc),
        )
        db.session.add(event)
