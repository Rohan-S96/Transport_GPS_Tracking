"""
Driver CRUD routes.
Prefix: /api/v1/drivers
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app.extensions import db
from app.models.driver import Driver
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.decorators import handle_service_errors, min_role

driver_bp = Blueprint("drivers", __name__, url_prefix="/api/v1/drivers")


@driver_bp.route("", methods=["GET"])
@jwt_required()
def list_drivers():
    """List all drivers in the caller's organisation."""
    claims = get_jwt()
    org_id = claims.get("organization_id")
    role = claims.get("role", "viewer")
    search = request.args.get("search", "").strip()
    status = request.args.get("status")
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    query = Driver.query
    if role != "admin" and org_id:
        query = query.filter_by(organization_id=org_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Driver.first_name.ilike(like),
                Driver.last_name.ilike(like),
                Driver.license_number.ilike(like),
                Driver.phone_number.ilike(like),
            )
        )

    total = query.count()
    drivers = query.offset((page - 1) * limit).limit(limit).all()
    return paginated_response([d.to_dict() for d in drivers], page, limit, total)


@driver_bp.route("/<string:driver_id>", methods=["GET"])
@jwt_required()
def get_driver(driver_id: str):
    """Get a single driver by ID."""
    driver = _get_driver_or_404(driver_id)
    return success_response(driver.to_dict())


@driver_bp.route("", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def create_driver():
    """Register a new driver."""
    claims = get_jwt()
    data = request.get_json(silent=True) or {}

    for field in ("first_name", "last_name", "license_number", "phone_number"):
        if not data.get(field):
            return error_response(f"'{field}' is required", 422)

    lic = data["license_number"].strip()
    if Driver.query.filter_by(license_number=lic).first():
        return error_response(f"Driver with license '{lic}' already exists", 409)

    from datetime import date
    expiry = None
    if data.get("license_expiry"):
        try:
            expiry = date.fromisoformat(data["license_expiry"])
        except ValueError:
            return error_response("license_expiry must be ISO date (YYYY-MM-DD)", 422)

    driver = Driver(
        organization_id=claims.get("organization_id"),
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        license_number=lic,
        license_expiry=expiry,
        phone_number=data["phone_number"].strip(),
        email=data.get("email"),
        status=data.get("status", "available"),
        notes=data.get("notes"),
    )
    db.session.add(driver)
    db.session.commit()
    return success_response(driver.to_dict(), message="Driver registered", code=201)


@driver_bp.route("/<string:driver_id>", methods=["PUT"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def update_driver(driver_id: str):
    """Update driver record."""
    driver = _get_driver_or_404(driver_id)
    data = request.get_json(silent=True) or {}

    updatable = (
        "first_name", "last_name", "phone_number", "email",
        "status", "notes", "safety_score",
    )
    for field in updatable:
        if field in data:
            setattr(driver, field, data[field])

    if "license_expiry" in data:
        from datetime import date
        try:
            driver.license_expiry = date.fromisoformat(data["license_expiry"])
        except ValueError:
            return error_response("license_expiry must be ISO date (YYYY-MM-DD)", 422)

    db.session.commit()
    return success_response(driver.to_dict(), message="Driver updated")


@driver_bp.route("/<string:driver_id>", methods=["DELETE"])
@jwt_required()
@min_role("fleet_manager")
def delete_driver(driver_id: str):
    """Remove a driver record."""
    driver = _get_driver_or_404(driver_id)
    db.session.delete(driver)
    db.session.commit()
    return success_response(None, message="Driver deleted")


def _get_driver_or_404(driver_id: str) -> Driver:
    d = Driver.query.get(driver_id)
    if not d:
        from flask import abort
        abort(404)
    return d
