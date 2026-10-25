"""
GPS Tracking routes.
Prefix: /api/v1/gps  (telemetry ingestion, live feed)
        /api/v1/trucks/<truck_id>/gps-history  (per-vehicle history)
"""
from datetime import datetime, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app.services.tracking_service import TrackingService
from app.utils.response_utils import success_response, error_response
from app.utils.decorators import handle_service_errors, min_role

tracking_bp = Blueprint("tracking", __name__)


# ── POST /api/v1/gps/locations ─────────────────────────────────────────────────

@tracking_bp.route("/api/v1/gps/locations", methods=["POST"])
@tracking_bp.route("/api/v1/tracking/telemetry", methods=["POST"])
@handle_service_errors
def ingest_gps_location():
    """
    Ingest a real-time GPS coordinate packet from a hardware tracker or SDK.

    Required body fields:
      latitude   : float  (-90 to 90)
      longitude  : float  (-180 to 180)

    Plus ONE of:
      vehicle_id  : UUID of the vehicle
      device_imei : 15-digit IMEI of the GPS device

    Optional:
      speed_kmh, heading, altitude, satellites, ignition,
      battery_pct, fuel_level_pct, timestamp (ISO-8601)
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    # Validate required fields
    if "latitude" not in data or "longitude" not in data:
        return error_response("latitude and longitude are required", 422)
    if not data.get("vehicle_id") and not data.get("device_imei"):
        return error_response("Provide vehicle_id or device_imei to identify the truck", 422)

    try:
        float(data["latitude"])
        float(data["longitude"])
    except (TypeError, ValueError):
        return error_response("latitude and longitude must be numeric", 422)

    result = TrackingService.process_telemetry(data)
    return success_response(result, message="GPS location recorded", code=201)


# ── GET /api/v1/gps/live ──────────────────────────────────────────────────────

@tracking_bp.route("/api/v1/gps/live", methods=["GET"])
@jwt_required()
def get_live_all():
    """Return the latest GPS position for every vehicle in the caller's org."""
    claims = get_jwt()
    org_id = claims.get("organization_id")
    role = claims.get("role", "viewer")

    # Admin sees everything; others see only their org
    fleet = TrackingService.get_live_fleet_positions(
        organization_id=None if role == "admin" else org_id
    )
    return success_response(fleet)


# ── GET /api/v1/gps/live/<truck_id> ───────────────────────────────────────────

@tracking_bp.route("/api/v1/gps/live/<string:truck_id>", methods=["GET"])
@jwt_required()
@handle_service_errors
def get_live_single(truck_id: str):
    """Return the latest GPS snapshot for a single truck."""
    data = TrackingService.get_live_truck_position(truck_id)
    return success_response(data)


# ── GET /api/v1/trucks/<truck_id>/gps-history ─────────────────────────────────

@tracking_bp.route("/api/v1/trucks/<string:truck_id>/gps-history", methods=["GET"])
@jwt_required()
@handle_service_errors
def get_gps_history(truck_id: str):
    """
    Return historical GPS trail for a truck.

    Query params (all optional):
      start_time : ISO-8601 datetime
      end_time   : ISO-8601 datetime
      limit      : integer (default 1000, max 5000)
    """
    def _parse_dt(val):
        if not val:
            return None
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None

    start_time = _parse_dt(request.args.get("start_time"))
    end_time = _parse_dt(request.args.get("end_time"))
    limit = min(int(request.args.get("limit", 1000)), 5000)

    trail = TrackingService.get_vehicle_gps_history(
        truck_id, start_time=start_time, end_time=end_time, limit=limit
    )
    return success_response(trail)


# ── POST /api/v1/gps/flag-offline (internal / admin only) ─────────────────────

@tracking_bp.route("/api/v1/gps/flag-offline", methods=["POST"])
@jwt_required()
@min_role("admin")
def flag_offline():
    """Manually trigger offline truck detection and alerting."""
    flagged = TrackingService.flag_offline_trucks()
    return success_response({"trucks_flagged_offline": flagged})
