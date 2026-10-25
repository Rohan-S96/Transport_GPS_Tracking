"""
Authentication routes — register, login, refresh, profile, logout.
Prefix: /api/v1/auth
"""
from flask import Blueprint, request
from flask_jwt_extended import (
    jwt_required, get_jwt_identity, get_jwt,
    create_access_token,
)
from app.services.auth_service import AuthService
from app.models.user import User, ROLES
from app.utils.response_utils import success_response, error_response
from app.utils.decorators import handle_service_errors

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/register", methods=["POST"])
@handle_service_errors
def register():
    """Register a new user and organisation (if provided)."""
    data = request.get_json(silent=True) or {}

    # Required fields
    missing = [f for f in ("email", "password", "first_name", "last_name") if not data.get(f)]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}", 422)

    password = data["password"]
    if len(password) < 8:
        return error_response("Password must be at least 8 characters", 422)

    role = data.get("role", "fleet_manager")
    if role not in ROLES:
        return error_response(f"Invalid role. Choose from: {', '.join(ROLES)}", 422)

    user = AuthService.register_user(
        email=data["email"],
        password=password,
        first_name=data["first_name"],
        last_name=data["last_name"],
        org_name=data.get("organization_name"),
        role=role,
    )
    return success_response(user.to_dict(), message="Account created successfully", code=201)


@auth_bp.route("/login", methods=["POST"])
@handle_service_errors
def login():
    """Authenticate and receive JWT access + refresh tokens."""
    data = request.get_json(silent=True) or {}

    if not data.get("email") or not data.get("password"):
        return error_response("email and password are required", 422)

    auth_data = AuthService.authenticate_user(data["email"], data["password"])
    return success_response(auth_data, message="Login successful")


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    """Exchange a valid refresh token for a new access token."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return error_response("User not found or deactivated", 401)

    new_token = create_access_token(
        identity=user.id,
        additional_claims={
            "role": user.role,
            "organization_id": user.organization_id,
            "full_name": user.full_name,
        },
    )
    return success_response(
        {"access_token": new_token, "token_type": "Bearer"},
        message="Token refreshed",
    )


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_profile():
    """Return the currently authenticated user's profile."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)
    return success_response(user.to_dict())


@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
@handle_service_errors
def update_profile():
    """Update first_name, last_name, or password."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 404)

    data = request.get_json(silent=True) or {}
    if "first_name" in data:
        user.first_name = data["first_name"].strip()
    if "last_name" in data:
        user.last_name = data["last_name"].strip()
    if "password" in data:
        if len(data["password"]) < 8:
            return error_response("Password must be at least 8 characters", 422)
        user.set_password(data["password"])

    from app.extensions import db
    db.session.commit()
    return success_response(user.to_dict(), message="Profile updated")
