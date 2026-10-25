"""
GPS Telemetry point model — high-frequency coordinate records.
"""
from datetime import datetime, timezone
from app.extensions import db


class GPSTelemetry(db.Model):
    """One timestamped GPS coordinate packet from a vehicle."""
    __tablename__ = "gps_telemetry"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    vehicle_id = db.Column(
        db.String(36),
        db.ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    altitude = db.Column(db.Float, nullable=True)
    speed_kmh = db.Column(db.Float, default=0.0, nullable=False)
    heading = db.Column(db.Float, default=0.0, nullable=False)
    satellites = db.Column(db.Integer, default=8, nullable=True)
    ignition = db.Column(db.Boolean, default=True, nullable=False)
    battery_pct = db.Column(db.Float, default=100.0, nullable=True)
    fuel_level_pct = db.Column(db.Float, nullable=True)
    odometer_km = db.Column(db.Float, nullable=True)
    # Raw packet from the GPS device (provider timestamp)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    # Server ingestion time
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        db.Index("idx_telemetry_vehicle_recorded", "vehicle_id", "recorded_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "altitude": round(self.altitude, 1) if self.altitude is not None else None,
            "speed_kmh": round(self.speed_kmh, 1),
            "heading": round(self.heading, 1),
            "satellites": self.satellites,
            "ignition": self.ignition,
            "battery_pct": round(self.battery_pct, 1) if self.battery_pct is not None else None,
            "fuel_level_pct": round(self.fuel_level_pct, 1) if self.fuel_level_pct is not None else None,
            "odometer_km": round(self.odometer_km, 1) if self.odometer_km is not None else None,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }
