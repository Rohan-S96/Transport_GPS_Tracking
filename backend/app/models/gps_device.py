"""
GPS Device model — hardware tracker installed in a vehicle.
"""
import uuid
from datetime import datetime, timezone
from app.extensions import db


class GPSDevice(db.Model):
    """Hardware GPS tracker/device bound to a single vehicle."""
    __tablename__ = "gps_devices"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = db.Column(
        db.String(36),
        db.ForeignKey("vehicles.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    imei = db.Column(db.String(30), unique=True, nullable=False, index=True)
    serial_number = db.Column(db.String(60), nullable=True)
    manufacturer = db.Column(db.String(60), nullable=True)
    model = db.Column(db.String(60), nullable=True)
    firmware_version = db.Column(db.String(30), nullable=True)
    sim_iccid = db.Column(db.String(30), nullable=True)
    sim_phone = db.Column(db.String(20), nullable=True)
    # active | inactive | decommissioned
    status = db.Column(db.String(20), default="active", nullable=False)
    installed_at = db.Column(db.Date, nullable=True)
    last_seen_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "imei": self.imei,
            "serial_number": self.serial_number,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "firmware_version": self.firmware_version,
            "sim_iccid": self.sim_iccid,
            "sim_phone": self.sim_phone,
            "status": self.status,
            "installed_at": self.installed_at.isoformat() if self.installed_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
