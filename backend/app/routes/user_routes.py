"""
User management CRUD routes.
Prefix: /api/v1/users
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app.extensions import db
from app.models.user import User, ROLES
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.decorators import handle_service_errors, min_role

user_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")


@user_bp.route("", methods=["GET"])
@jwt_required()
@min_role("fleet_manager")
def list_users():
    """List users in caller's organisation."""
    claims = get_jwt()
    org_id = claims.get("organization_id")
    role = claims.get("role", "viewer")
    search = request.args.get("search", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    query = User.query
    if role != "admin" and org_id:
        query = query.filter_by(organization_id=org_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.email.ilike(like),
            )
        )

    query = query.order_by(User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * limit).limit(limit).all()
    return paginated_response([u.to_dict() for u in users], page, limit, total)


@user_bp.route("/<string:user_id>", methods=["GET"])
@jwt_required()
@min_role("fleet_manager")
def get_user(user_id: str):
    """Get single user profile."""
    user = _get_user_or_404(user_id)
    return success_response(user.to_dict())


@user_bp.route("", methods=["POST"])
@jwt_required()
@min_role("admin")
@handle_service_errors
def create_user():
    """Create a new user with specified role."""
    claims = get_jwt()
    data = request.get_json(silent=True) or {}

    missing = [f for f in ("email", "password", "first_name", "last_name") if not data.get(f)]
    if missing:
        return error_response(f"Missing required fields: {', '.join(missing)}", 422)

    if len(data["password"]) < 8:
        return error_response("Password must be at least 8 characters", 422)

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return error_response(f"User with email '{email}' already exists", 409)

    role = data.get("role", "viewer")
    if role not in ROLES:
        return error_response(f"Invalid role. Choose from: {', '.join(ROLES)}", 422)

    user = User(
        organization_id=claims.get("organization_id"),
        email=email,
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        role=role,
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return success_response(user.to_dict(), message="User created successfully", code=201)


@user_bp.route("/<string:user_id>", methods=["PUT"])
@jwt_required()
@min_role("admin")
@handle_service_errors
def update_user(user_id: str):
    """Update user role, status or details."""
    user = _get_user_or_404(user_id)
    data = request.get_json(silent=True) or {}

    if "first_name" in data:
        user.first_name = data["first_name"].strip()
    if "last_name" in data:
        user.last_name = data["last_name"].strip()
    if "role" in data:
        if data["role"] in ROLES:
            user.role = data["role"]
        else:
            return error_response(f"Invalid role: {data['role']}", 422)
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "password" in data and data["password"]:
        if len(data["password"]) < 8:
            return error_response("Password must be at least 8 characters", 422)
        user.set_password(data["password"])

    db.session.commit()
    return success_response(user.to_dict(), message="User updated successfully")


@user_bp.route("/<string:user_id>", methods=["DELETE"])
@jwt_required()
@min_role("admin")
@handle_service_errors
def delete_user(user_id: str):
    """Deactivate or remove user."""
    user = _get_user_or_404(user_id)
    user.is_active = False
    db.session.commit()
    return success_response(message="User deactivated")


def _get_user_or_404(user_id: str) -> User:
    user = User.query.get(user_id)
    if not user:
        from flask import abort
        abort(404)
    return user
