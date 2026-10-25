"""
Maintenance and Fuel log SQLAlchemy models.
"""
import uuid
from datetime import datetime, date, timezone
from app.extensions import db

class MaintenanceLog(db.Model):
    """Vehicle service and repair maintenance log."""
    __tablename__ = "maintenance_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = db.Column(db.String(36), db.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    service_type = db.Column(db.String(80), nullable=False)
    odometer_at_service = db.Column(db.Float, nullable=False)
    cost_amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    service_date = db.Column(db.Date, default=date.today, nullable=False)
    next_due_odometer = db.Column(db.Float, nullable=True)
    next_due_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "registration_number": self.vehicle.registration_number if self.vehicle else None,
            "service_type": self.service_type,
            "odometer_at_service": round(self.odometer_at_service, 1),
            "cost_amount": float(self.cost_amount),
            "service_date": self.service_date.isoformat() if self.service_date else None,
            "next_due_odometer": round(self.next_due_odometer, 1) if self.next_due_odometer else None,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FuelLog(db.Model):
    """Refueling transaction and volume log."""
    __tablename__ = "fuel_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = db.Column(db.String(36), db.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    litres_filled = db.Column(db.Float, nullable=False)
    total_cost = db.Column(db.Numeric(10, 2), nullable=False)
    odometer_km = db.Column(db.Float, nullable=False)
    fuel_station = db.Column(db.String(120), nullable=True)
    filled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "vehicle_id": self.vehicle_id,
            "registration_number": self.vehicle.registration_number if self.vehicle else None,
            "litres_filled": round(self.litres_filled, 2),
            "total_cost": float(self.total_cost),
            "odometer_km": round(self.odometer_km, 1),
            "fuel_station": self.fuel_station,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None,
        }
