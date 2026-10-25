"""
Driver SQLAlchemy model — commercial truck drivers.
"""
import uuid
from datetime import datetime, timezone
from app.extensions import db


class Driver(db.Model):
    """Driver entity, assigned to vehicles and trips."""
    __tablename__ = "drivers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(
        db.String(36),
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    first_name = db.Column(db.String(60), nullable=False)
    last_name = db.Column(db.String(60), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    license_expiry = db.Column(db.Date, nullable=True)
    phone_number = db.Column(db.String(25), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    # Safety score 0–100 computed from trip events (overspeed, harsh braking …)
    safety_score = db.Column(db.Float, default=100.0, nullable=False)
    # available | on_trip | off_duty | suspended
    status = db.Column(db.String(20), default="available", nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ──────────────────────────────────────────────────────────
    vehicles = db.relationship("Vehicle", backref="assigned_driver", lazy="dynamic")
    trips = db.relationship("Trip", backref="driver", lazy="dynamic")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "name": self.full_name,
            "license_number": self.license_number,
            "license_expiry": self.license_expiry.isoformat() if self.license_expiry else None,
            "phone_number": self.phone_number,
            "email": self.email,
            "safety_score": round(self.safety_score, 1),
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
