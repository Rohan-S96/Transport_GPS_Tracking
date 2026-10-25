"""
Report Export and Audit Log SQLAlchemy models.
"""
import uuid
from datetime import datetime, timezone
from app.extensions import db


class ReportExport(db.Model):
    """Tracks every Excel/CSV report generated from the system."""
    __tablename__ = "report_exports"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(
        db.String(36),
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    requested_by = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    # vehicles | trips | alerts | drivers | fuel | maintenance
    report_type = db.Column(db.String(30), nullable=False)
    # excel | csv
    format = db.Column(db.String(10), default="excel", nullable=False)
    # pending | completed | failed
    status = db.Column(db.String(15), default="completed", nullable=False)
    filter_params = db.Column(db.Text, nullable=True)   # JSON-encoded request params
    row_count = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "requested_by": self.requested_by,
            "report_type": self.report_type,
            "format": self.format,
            "status": self.status,
            "row_count": self.row_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(db.Model):
    """Immutable record of significant user actions for security audit."""
    __tablename__ = "audit_logs"

    id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    organization_id = db.Column(
        db.String(36),
        db.ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True, index=True
    )
    # Action performed: login, logout, create_vehicle, delete_driver, etc.
    action = db.Column(db.String(60), nullable=False)
    # Entity type acted upon: vehicle, driver, trip, geofence, user, …
    entity_type = db.Column(db.String(40), nullable=True)
    entity_id = db.Column(db.String(36), nullable=True)
    # JSON payload capturing the relevant before/after data
    detail = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)   # IPv4 or IPv6
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_email": self.user.email if self.user else None,
            "organization_id": self.organization_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "detail": self.detail,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
