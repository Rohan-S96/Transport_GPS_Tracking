"""
Validation schemas for alerts and acknowledgments.
"""
from marshmallow import Schema, fields

class AcknowledgeAlertSchema(Schema):
    notes = fields.String(required=False, allow_none=True)
