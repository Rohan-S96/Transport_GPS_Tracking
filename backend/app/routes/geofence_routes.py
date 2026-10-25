"""
Geofence CRUD routes.
Prefix: /api/v1/geofences
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app.extensions import db
from app.models.geofence import Geofence
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.decorators import handle_service_errors, min_role
from app.services.geofence_service import GeofenceService

geofence_bp = Blueprint("geofences", __name__, url_prefix="/api/v1/geofences")


@geofence_bp.route("", methods=["GET"])
@jwt_required()
def list_geofences():
    """List geofences for the caller's organisation."""
    claims = get_jwt()
    org_id = claims.get("organization_id")
    role = claims.get("role", "viewer")
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    query = Geofence.query
    if role != "admin" and org_id:
        query = query.filter_by(organization_id=org_id)
    is_active = request.args.get("is_active")
    if is_active is not None:
        query = query.filter_by(is_active=(is_active.lower() == "true"))

    total = query.count()
    fences = query.offset((page - 1) * limit).limit(limit).all()
    return paginated_response([f.to_dict() for f in fences], page, limit, total)


@geofence_bp.route("/<string:fence_id>", methods=["GET"])
@jwt_required()
def get_geofence(fence_id: str):
    """Get a single geofence."""
    fence = _get_fence_or_404(fence_id)
    return success_response(fence.to_dict())


@geofence_bp.route("", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def create_geofence():
    """Create a new geofence zone."""
    claims = get_jwt()
    data = request.get_json(silent=True) or {}

    if not data.get("name"):
        return error_response("'name' is required", 422)

    fence_type = data.get("fence_type", "circle")
    if fence_type not in ("circle", "polygon"):
        return error_response("fence_type must be 'circle' or 'polygon'", 422)

    fence = Geofence(
        organization_id=claims.get("organization_id"),
        name=data["name"].strip(),
        description=data.get("description"),
        fence_type=fence_type,
        alert_on_entry=data.get("alert_on_entry", True),
        alert_on_exit=data.get("alert_on_exit", True),
        is_active=data.get("is_active", True),
        color_hex=data.get("color_hex", "#3B82F6"),
    )

    if fence_type == "circle":
        for field in ("center_latitude", "center_longitude", "radius_meters"):
            if data.get(field) is None:
                return error_response(f"'{field}' is required for circle geofence", 422)
        fence.center_latitude = float(data["center_latitude"])
        fence.center_longitude = float(data["center_longitude"])
        fence.radius_meters = float(data["radius_meters"])
    else:
        coords = data.get("coordinates", [])
        if len(coords) < 3:
            return error_response("polygon geofence requires at least 3 coordinate pairs", 422)
        fence.coordinates = coords

    db.session.add(fence)
    db.session.commit()
    return success_response(fence.to_dict(), message="Geofence created", code=201)


@geofence_bp.route("/<string:fence_id>", methods=["PUT"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def update_geofence(fence_id: str):
    """Update geofence properties."""
    fence = _get_fence_or_404(fence_id)
    data = request.get_json(silent=True) or {}

    updatable = (
        "name", "description", "alert_on_entry", "alert_on_exit",
        "is_active", "color_hex", "center_latitude", "center_longitude",
        "radius_meters",
    )
    for field in updatable:
        if field in data:
            setattr(fence, field, data[field])
    if "coordinates" in data:
        fence.coordinates = data["coordinates"]

    db.session.commit()
    return success_response(fence.to_dict(), message="Geofence updated")


@geofence_bp.route("/<string:fence_id>", methods=["DELETE"])
@jwt_required()
@min_role("fleet_manager")
def delete_geofence(fence_id: str):
    """Delete a geofence."""
    fence = _get_fence_or_404(fence_id)
    db.session.delete(fence)
    db.session.commit()
    return success_response(None, message="Geofence deleted")


@geofence_bp.route("/<string:fence_id>/check", methods=["POST"])
@jwt_required()
@handle_service_errors
def check_point_in_fence(fence_id: str):
    """Check if a lat/lng coordinate falls inside this geofence."""
    fence = _get_fence_or_404(fence_id)
    data = request.get_json(silent=True) or {}
    lat = data.get("latitude")
    lng = data.get("longitude")
    if lat is None or lng is None:
        return error_response("latitude and longitude are required", 422)
    inside = GeofenceService.is_inside(float(lat), float(lng), fence)
    return success_response({"inside": inside, "geofence_id": fence_id, "geofence_name": fence.name})


def _get_fence_or_404(fence_id: str) -> Geofence:
    f = Geofence.query.get(fence_id)
    if not f:
        from flask import abort
        abort(404)
    return f
