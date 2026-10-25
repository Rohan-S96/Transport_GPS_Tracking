"""
Vehicle (Truck) CRUD routes.
Prefix: /api/v1/vehicles
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app.extensions import db
from app.models.vehicle import Vehicle
from app.models.gps_device import GPSDevice
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.decorators import handle_service_errors, min_role

vehicle_bp = Blueprint("vehicles", __name__, url_prefix="/api/v1/vehicles")


@vehicle_bp.route("", methods=["GET"])
@jwt_required()
def list_vehicles():
    """List vehicles with optional filters. Scoped to caller's org."""
    claims = get_jwt()
    org_id = claims.get("organization_id")
    role = claims.get("role", "viewer")

    status = request.args.get("status")
    search = request.args.get("search", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))
    include_telemetry = request.args.get("include_telemetry", "false").lower() == "true"

    query = Vehicle.query
    if role != "admin" and org_id:
        query = query.filter_by(organization_id=org_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Vehicle.registration_number.ilike(like),
                Vehicle.make.ilike(like),
                Vehicle.model.ilike(like),
            )
        )

    total = query.count()
    vehicles = query.offset((page - 1) * limit).limit(limit).all()
    results = [v.to_dict(include_telemetry=include_telemetry, include_device=True) for v in vehicles]
    return paginated_response(results, page, limit, total)


@vehicle_bp.route("/<string:vehicle_id>", methods=["GET"])
@jwt_required()
@handle_service_errors
def get_vehicle(vehicle_id: str):
    """Get full details for a single vehicle."""
    vehicle = _get_vehicle_or_404(vehicle_id)
    return success_response(vehicle.to_dict(include_telemetry=True, include_device=True))


@vehicle_bp.route("", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def create_vehicle():
    """Register a new truck in the fleet."""
    claims = get_jwt()
    data = request.get_json(silent=True) or {}

    for field in ("registration_number", "make", "model"):
        if not data.get(field):
            return error_response(f"'{field}' is required", 422)

    reg = data["registration_number"].strip().upper()
    if Vehicle.query.filter_by(registration_number=reg).first():
        return error_response(
            f"Vehicle with registration '{reg}' already exists", 409
        )

    vehicle = Vehicle(
        organization_id=claims.get("organization_id"),
        registration_number=reg,
        vin=data.get("vin"),
        make=data["make"].strip(),
        model=data["model"].strip(),
        year=data.get("year"),
        color=data.get("color"),
        fuel_type=data.get("fuel_type", "diesel"),
        fuel_capacity_litres=data.get("fuel_capacity_litres", 300.0),
        assigned_driver_id=data.get("assigned_driver_id"),
        speed_limit_kmh=data.get("speed_limit_kmh"),
        notes=data.get("notes"),
        status=data.get("status", "active"),
    )
    db.session.add(vehicle)
    db.session.flush()  # get vehicle.id

    # Optionally create a GPS device record
    imei = data.get("device_imei")
    if imei:
        if GPSDevice.query.filter_by(imei=str(imei)).first():
            db.session.rollback()
            return error_response(f"IMEI '{imei}' is already registered to another vehicle", 409)
        device = GPSDevice(
            vehicle_id=vehicle.id,
            imei=str(imei).strip(),
        )
        db.session.add(device)

    db.session.commit()
    return success_response(
        vehicle.to_dict(include_device=True),
        message="Vehicle registered successfully",
        code=201,
    )


@vehicle_bp.route("/<string:vehicle_id>", methods=["PUT"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def update_vehicle(vehicle_id: str):
    """Update vehicle fields."""
    vehicle = _get_vehicle_or_404(vehicle_id)
    data = request.get_json(silent=True) or {}

    updatable = (
        "make", "model", "year", "color", "fuel_type",
        "fuel_capacity_litres", "status", "assigned_driver_id",
        "speed_limit_kmh", "notes", "vin",
    )
    for field in updatable:
        if field in data:
            setattr(vehicle, field, data[field])

    db.session.commit()
    return success_response(vehicle.to_dict(include_device=True), message="Vehicle updated")


@vehicle_bp.route("/<string:vehicle_id>", methods=["DELETE"])
@jwt_required()
@min_role("fleet_manager")
def delete_vehicle(vehicle_id: str):
    """Remove a vehicle from the fleet (cascades to telemetry, alerts, trips)."""
    vehicle = _get_vehicle_or_404(vehicle_id)
    db.session.delete(vehicle)
    db.session.commit()
    return success_response(None, message="Vehicle deleted successfully")


# ── GPS Device sub-resource ────────────────────────────────────────────────────

@vehicle_bp.route("/<string:vehicle_id>/device", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def assign_gps_device(vehicle_id: str):
    """Assign or replace the GPS device IMEI for a vehicle."""
    vehicle = _get_vehicle_or_404(vehicle_id)
    data = request.get_json(silent=True) or {}
    imei = data.get("imei", "").strip()
    if not imei:
        return error_response("imei is required", 422)

    existing = GPSDevice.query.filter_by(imei=imei).first()
    if existing and existing.vehicle_id != vehicle_id:
        return error_response(f"IMEI '{imei}' is already assigned to another vehicle", 409)

    if vehicle.gps_device:
        vehicle.gps_device.imei = imei
        for field in ("serial_number", "manufacturer", "model", "firmware_version",
                      "sim_iccid", "sim_phone", "status", "installed_at"):
            if field in data:
                setattr(vehicle.gps_device, field, data[field])
    else:
        device = GPSDevice(vehicle_id=vehicle_id, imei=imei)
        for field in ("serial_number", "manufacturer", "model", "firmware_version",
                      "sim_iccid", "sim_phone", "installed_at"):
            if field in data:
                setattr(device, field, data[field])
        db.session.add(device)

    db.session.commit()
    return success_response(
        vehicle.to_dict(include_device=True),
        message="GPS device assigned",
    )


# ── Private helper ─────────────────────────────────────────────────────────────

def _get_vehicle_or_404(vehicle_id: str) -> Vehicle:
    v = Vehicle.query.get(vehicle_id)
    if not v:
        from flask import abort
        abort(404)
    return v
