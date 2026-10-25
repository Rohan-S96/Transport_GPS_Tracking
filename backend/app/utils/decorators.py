"""
Route decorators for role-based access control and uniform error handling.

Roles (least to most privileged):
  viewer        — read-only access to fleet data
  driver        — can view own trips; GPS ingestion
  fleet_manager — full fleet CRUD
  admin         — full system access including org management and audit logs
"""
from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request, get_jwt
from app.utils.response_utils import error_response

# Role hierarchy — higher index = more privileged
_ROLE_HIERARCHY = ["viewer", "driver", "fleet_manager", "admin"]


def role_required(*allowed_roles: str):
    """
    Restrict endpoint to specific roles.
    Usage: @role_required("admin", "fleet_manager")
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role", "viewer")
            if user_role not in allowed_roles:
                return error_response(
                    f"Access denied. Required role(s): {', '.join(allowed_roles)}",
                    403,
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def min_role(minimum_role: str):
    """
    Allow access if user's role is >= minimum_role in the hierarchy.
    Usage: @min_role("fleet_manager")  # allows fleet_manager and admin
    """
    min_index = _ROLE_HIERARCHY.index(minimum_role) if minimum_role in _ROLE_HIERARCHY else 0

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role", "viewer")
            role_index = _ROLE_HIERARCHY.index(user_role) if user_role in _ROLE_HIERARCHY else 0
            if role_index < min_index:
                return error_response(
                    f"Access denied. Minimum required role: {minimum_role}",
                    403,
                )
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def org_isolation(fn):
    """
    Inject organization_id from the JWT claims into kwargs so route handlers
    can filter data to the caller's organization.
    Non-admin users can only see their own org's data.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        kwargs["_org_id"] = claims.get("organization_id")
        kwargs["_role"] = claims.get("role", "viewer")
        return fn(*args, **kwargs)
    return wrapper


def handle_service_errors(fn):
    """Catch ValueError / generic exceptions from service layer and return JSON."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as ve:
            return error_response(str(ve), 400)
        except Exception as e:
            # Log full traceback in development
            import traceback
            traceback.print_exc()
            return error_response("An internal error occurred", 500, details=str(e))
    return wrapper
