"""
Vehicle (Truck) SQLAlchemy model — commercial fleet asset.
"""
import uuid
from datetime import datetime, timezone
from app.extensions import db


class Vehicle(db.Model):
    """Fleet truck / vehicle entity."""
    __tablename__ = "vehicles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(
        db.String(36),
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    assigned_driver_id = db.Column(
        db.String(36),
        db.ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True
    )
    registration_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    vin = db.Column(db.String(50), unique=True, nullable=True)
    make = db.Column(db.String(60), nullable=False)
    model = db.Column(db.String(60), nullable=False)
    year = db.Column(db.Integer, nullable=True)
    color = db.Column(db.String(30), nullable=True)
    # diesel | petrol | electric | cng | hybrid
    fuel_type = db.Column(db.String(20), default="diesel", nullable=False)
    fuel_capacity_litres = db.Column(db.Float, default=300.0, nullable=False)
    # active | idle | maintenance | offline | decommissioned
    status = db.Column(db.String(20), default="active", nullable=False)
    current_odometer_km = db.Column(db.Float, default=0.0, nullable=False)
    # Speed limit override for this specific vehicle (null = org default)
    speed_limit_kmh = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ──────────────────────────────────────────────────────────
    gps_device = db.relationship(
        "GPSDevice", backref="vehicle", uselist=False,
        cascade="all, delete-orphan"
    )
    telemetry = db.relationship(
        "GPSTelemetry", backref="vehicle",
        lazy="dynamic", cascade="all, delete-orphan"
    )
    alerts = db.relationship(
        "Alert", backref="vehicle",
        lazy="dynamic", cascade="all, delete-orphan"
    )
    trips = db.relationship(
        "Trip", backref="vehicle",
        lazy="dynamic", cascade="all, delete-orphan"
    )
    maintenance_logs = db.relationship(
        "MaintenanceLog", backref="vehicle",
        lazy="dynamic", cascade="all, delete-orphan"
    )
    fuel_logs = db.relationship(
        "FuelLog", backref="vehicle",
        lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self, include_telemetry: bool = False, include_device: bool = False):
        data = {
            "id": self.id,
            "organization_id": self.organization_id,
            "registration_number": self.registration_number,
            "vin": self.vin,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "color": self.color,
            "fuel_type": self.fuel_type,
            "fuel_capacity_litres": self.fuel_capacity_litres,
            "status": self.status,
            "current_odometer_km": round(self.current_odometer_km, 1),
            "speed_limit_kmh": self.speed_limit_kmh,
            "notes": self.notes,
            "assigned_driver": self.assigned_driver.to_dict() if self.assigned_driver else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_telemetry:
            last_point = (
                self.telemetry
                .order_by(db.text("recorded_at DESC"))
                .first()
            )
            data["last_known_telemetry"] = last_point.to_dict() if last_point else None
        if include_device:
            data["gps_device"] = self.gps_device.to_dict() if self.gps_device else None
        return data
