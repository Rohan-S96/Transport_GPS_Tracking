"""
Database models package — imports all models so SQLAlchemy can discover them
and Flask-Migrate can generate migrations automatically.
"""
from app.models.user import Organization, User
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.gps_device import GPSDevice
from app.models.gps_telemetry import GPSTelemetry
from app.models.geofence import Geofence
from app.models.alert import Alert
from app.models.trip import Trip, TripEvent, Stop
from app.models.maintenance import MaintenanceLog, FuelLog
from app.models.company import Company, CompanyLocation
from app.models.audit import ReportExport, AuditLog

__all__ = [
    "Organization",
    "User",
    "Driver",
    "Vehicle",
    "GPSDevice",
    "GPSTelemetry",
    "Geofence",
    "Alert",
    "Trip",
    "TripEvent",
    "Stop",
    "MaintenanceLog",
    "FuelLog",
    "Company",
    "CompanyLocation",
    "ReportExport",
    "AuditLog",
]
