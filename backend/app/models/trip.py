"""
Trip, TripEvent, and Stop SQLAlchemy models.
"""
import uuid
from datetime import datetime, timezone
from app.extensions import db


class Trip(db.Model):
    """A vehicle journey segment from ignition-on to ignition-off."""
    __tablename__ = "trips"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(
        db.String(36),
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    vehicle_id = db.Column(
        db.String(36),
        db.ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    driver_id = db.Column(
        db.String(36),
        db.ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True
    )
    # in_progress | completed | cancelled
    status = db.Column(db.String(20), default="in_progress", nullable=False)
    # loaded | empty
    load_status = db.Column(db.String(20), default="empty", nullable=True)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True), nullable=True)
    start_latitude = db.Column(db.Float, nullable=False)
    start_longitude = db.Column(db.Float, nullable=False)
    end_latitude = db.Column(db.Float, nullable=True)
    end_longitude = db.Column(db.Float, nullable=True)
    distance_km = db.Column(db.Float, default=0.0, nullable=False)
    duration_minutes = db.Column(db.Float, default=0.0, nullable=False)
    idle_minutes = db.Column(db.Float, default=0.0, nullable=False)
    max_speed_kmh = db.Column(db.Float, default=0.0, nullable=False)
    avg_speed_kmh = db.Column(db.Float, default=0.0, nullable=False)
    fuel_consumed_litres = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ──────────────────────────────────────────────────────────
    events = db.relationship(
        "TripEvent", backref="trip",
        lazy="dynamic", cascade="all, delete-orphan",
        order_by="TripEvent.occurred_at"
    )
    stops = db.relationship(
        "Stop", backref="trip",
        lazy="dynamic", cascade="all, delete-orphan",
        order_by="Stop.arrived_at"
    )

    def to_dict(self, include_stops: bool = False):
        data = {
            "id": self.id,
            "organization_id": self.organization_id,
            "vehicle_id": self.vehicle_id,
            "registration_number": self.vehicle.registration_number if self.vehicle else None,
            "driver_id": self.driver_id,
            "driver_name": self.driver.full_name if self.driver else None,
            "status": self.status,
            "load_status": self.load_status or "empty",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "start_location": {"lat": self.start_latitude, "lng": self.start_longitude},
            "end_location": (
                {"lat": self.end_latitude, "lng": self.end_longitude}
                if self.end_latitude is not None else None
            ),
            "distance_km": round(self.distance_km, 2),
            "duration_minutes": round(self.duration_minutes, 1),
            "idle_minutes": round(self.idle_minutes, 1),
            "max_speed_kmh": round(self.max_speed_kmh, 1),
            "avg_speed_kmh": round(self.avg_speed_kmh, 1),
            "fuel_consumed_litres": (
                round(self.fuel_consumed_litres, 2)
                if self.fuel_consumed_litres is not None else None
            ),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_stops:
            data["stops"] = [s.to_dict() for s in self.stops.all()]
        return data


# ── Event types ───────────────────────────────────────────────────────────────
TRIP_EVENT_TYPES = (
    "trip_start", "trip_end", "trip_cancel",
    "overspeed", "harsh_brake", "harsh_acceleration",
    "geofence_entry", "geofence_exit",
    "sos", "engine_on", "engine_off",
)


class TripEvent(db.Model):
    """A discrete event that occurred during a trip (overspeed, harsh-brake, etc.)."""
    __tablename__ = "trip_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = db.Column(
        db.String(36),
        db.ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    vehicle_id = db.Column(
        db.String(36),
        db.ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    event_type = db.Column(db.String(30), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    speed_kmh = db.Column(db.Float, nullable=True)
    heading = db.Column(db.Float, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    occurred_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "vehicle_id": self.vehicle_id,
            "event_type": self.event_type,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "speed_kmh": self.speed_kmh,
            "heading": self.heading,
            "description": self.description,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
        }


class Stop(db.Model):
    """A detected stationary period within a trip (duration >= configured min)."""
    __tablename__ = "stops"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = db.Column(
        db.String(36),
        db.ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    vehicle_id = db.Column(
        db.String(36),
        db.ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    arrived_at = db.Column(db.DateTime(timezone=True), nullable=False)
    departed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    duration_minutes = db.Column(db.Float, default=0.0, nullable=False)
    address = db.Column(db.String(255), nullable=True)  # reverse-geocode result
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "vehicle_id": self.vehicle_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "arrived_at": self.arrived_at.isoformat() if self.arrived_at else None,
            "departed_at": self.departed_at.isoformat() if self.departed_at else None,
            "duration_minutes": round(self.duration_minutes, 1),
            "address": self.address,
        }
