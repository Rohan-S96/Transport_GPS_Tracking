"""
Validation schemas for authentication and user accounts.
"""
from marshmallow import Schema, fields, validate

class RegisterUserSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=8, max=100))
    first_name = fields.String(required=True, validate=validate.Length(min=1, max=60))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=60))
    organization_name = fields.String(required=False, allow_none=True)
    role = fields.String(required=False, validate=validate.OneOf(["admin", "manager", "dispatcher", "driver"]))


class LoginUserSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True)
