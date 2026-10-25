"""
Validation schemas for raw GPS packet ingestion.
"""
from marshmallow import Schema, fields, validate

class TelemetryIngestSchema(Schema):
    vehicle_id = fields.String(required=False, allow_none=True)
    device_imei = fields.String(required=False, allow_none=True)
    latitude = fields.Float(required=True, validate=validate.Range(min=-90.0, max=90.0))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180.0, max=180.0))
    altitude = fields.Float(required=False, allow_none=True)
    speed_kmh = fields.Float(required=False, validate=validate.Range(min=0.0))
    speed = fields.Float(required=False)
    heading = fields.Float(required=False, validate=validate.Range(min=0.0, max=360.0))
    satellites = fields.Integer(required=False)
    ignition = fields.Boolean(required=False)
    battery_pct = fields.Float(required=False)
    fuel_level_pct = fields.Float(required=False, allow_none=True)
    timestamp = fields.String(required=False, allow_none=True)
