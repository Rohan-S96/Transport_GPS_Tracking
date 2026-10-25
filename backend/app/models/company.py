"""
Company and CompanyLocation models.
Companies are freight/cargo customers that vehicles deliver to/from.
"""
import uuid
from datetime import datetime, timezone
from app.extensions import db


class Company(db.Model):
    """
    Freight customer / transport client company.
    Linked to a fleet Organization.
    """
    __tablename__ = "companies"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(
        db.String(36),
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    name = db.Column(db.String(120), nullable=False)
    contact_person = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_phone = db.Column(db.String(25), nullable=True)
    gst_number = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # ── Relationships ──────────────────────────────────────────────────────────
    locations = db.relationship(
        "CompanyLocation", backref="company",
        lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self, include_locations: bool = False):
        data = {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
            "contact_person": self.contact_person,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "gst_number": self.gst_number,
            "is_active": self.is_active,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_locations:
            data["locations"] = [loc.to_dict() for loc in self.locations.all()]
        return data


class CompanyLocation(db.Model):
    """
    A physical pickup / delivery site for a Company.
    Can be a geofenced area — linked to an optional Geofence.
    """
    __tablename__ = "company_locations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = db.Column(
        db.String(36),
        db.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    geofence_id = db.Column(
        db.String(36),
        db.ForeignKey("geofences.id", ondelete="SET NULL"),
        nullable=True
    )
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    state = db.Column(db.String(80), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    # warehouse | office | depot | port | other
    location_type = db.Column(db.String(30), default="warehouse", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "geofence_id": self.geofence_id,
            "name": self.name,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "location_type": self.location_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
