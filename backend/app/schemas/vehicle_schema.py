"""
Validation schemas for fleet vehicle resources.
"""
from marshmallow import Schema, fields, validate

class VehicleSchema(Schema):
    registration_number = fields.String(required=True, validate=validate.Length(min=3, max=30))
    make = fields.String(required=True, validate=validate.Length(min=2, max=60))
    model = fields.String(required=True, validate=validate.Length(min=1, max=60))
    year = fields.Integer(required=False, allow_none=True)
    vin = fields.String(required=False, allow_none=True)
    device_imei = fields.String(required=False, allow_none=True)
    fuel_type = fields.String(required=False, validate=validate.OneOf(["diesel", "petrol", "electric", "cng"]))
    fuel_capacity_litres = fields.Float(required=False)
    assigned_driver_id = fields.String(required=False, allow_none=True)
    status = fields.String(required=False, validate=validate.OneOf(["active", "idle", "maintenance", "offline"]))
