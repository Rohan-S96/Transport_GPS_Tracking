"""
Schemas package exports.
"""
from app.schemas.user_schema import RegisterUserSchema, LoginUserSchema
from app.schemas.vehicle_schema import VehicleSchema
from app.schemas.telemetry_schema import TelemetryIngestSchema
from app.schemas.geofence_schema import GeofenceSchema
from app.schemas.alert_schema import AcknowledgeAlertSchema

__all__ = [
    "RegisterUserSchema",
    "LoginUserSchema",
    "VehicleSchema",
    "TelemetryIngestSchema",
    "GeofenceSchema",
    "AcknowledgeAlertSchema",
]
