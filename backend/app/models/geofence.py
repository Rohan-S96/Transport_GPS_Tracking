"""
Geofence model — circular and polygon virtual boundary zones.
"""
import uuid
import json
from datetime import datetime, timezone
from app.extensions import db


class Geofence(db.Model):
    """Geographic boundary zone with configurable alert rules."""
    __tablename__ = "geofences"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(
        db.String(36),
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    # circle | polygon
    fence_type = db.Column(db.String(20), default="circle", nullable=False)
    # Circle fields
    center_latitude = db.Column(db.Float, nullable=True)
    center_longitude = db.Column(db.Float, nullable=True)
    radius_meters = db.Column(db.Float, nullable=True)
    # Polygon fields — stored as JSON [[lat,lng], ...]
    coordinates_json = db.Column(db.Text, nullable=True)
    # Alert behaviour
    alert_on_entry = db.Column(db.Boolean, default=True, nullable=False)
    alert_on_exit = db.Column(db.Boolean, default=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    color_hex = db.Column(db.String(10), default="#3B82F6", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ──────────────────────────────────────────────────────────
    alerts = db.relationship("Alert", backref="geofence", lazy="dynamic")

    # ── Coordinate property helper ─────────────────────────────────────────────
    @property
    def coordinates(self):
        if self.coordinates_json:
            try:
                return json.loads(self.coordinates_json)
            except Exception:
                return []
        return []

    @coordinates.setter
    def coordinates(self, value):
        if isinstance(value, (list, dict)):
            self.coordinates_json = json.dumps(value)
        else:
            self.coordinates_json = str(value) if value else None

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "description": self.description,
            "fence_type": self.fence_type,
            "center_latitude": self.center_latitude,
            "center_longitude": self.center_longitude,
            "radius_meters": self.radius_meters,
            "coordinates": self.coordinates,
            "alert_on_entry": self.alert_on_entry,
            "alert_on_exit": self.alert_on_exit,
            "is_active": self.is_active,
            "color_hex": self.color_hex,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
