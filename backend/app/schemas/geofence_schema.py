"""
Validation schema for Geofences.
"""
from marshmallow import Schema, fields, validate

class GeofenceSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    fence_type = fields.String(required=True, validate=validate.OneOf(["circle", "polygon"]))
    center_latitude = fields.Float(required=False, allow_none=True)
    center_longitude = fields.Float(required=False, allow_none=True)
    radius_meters = fields.Float(required=False, allow_none=True)
    coordinates = fields.List(fields.List(fields.Float()), required=False, allow_none=True)
    alert_on_entry = fields.Boolean(required=False)
    alert_on_exit = fields.Boolean(required=False)
    color_hex = fields.String(required=False)
