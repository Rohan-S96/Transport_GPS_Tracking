"""
Trip routes — start, complete, cancel, events, stops, history.
Prefix: /api/v1/trips
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app.services.trip_service import TripService
from app.services.tracking_service import TrackingService
from app.models.trip import Trip, TripEvent, Stop, TRIP_EVENT_TYPES
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.decorators import handle_service_errors, min_role

trip_bp = Blueprint("trips", __name__, url_prefix="/api/v1/trips")


@trip_bp.route("", methods=["GET"])
@jwt_required()
def list_trips():
    """List trips with optional vehicle_id filter and pagination."""
    claims = get_jwt()
    org_id = claims.get("organization_id")
    role = claims.get("role", "viewer")

    vehicle_id = request.args.get("vehicle_id")
    status = request.args.get("status")
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    query = Trip.query
    if role != "admin" and org_id:
        query = query.filter_by(organization_id=org_id)
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Trip.start_time.desc())
    total = query.count()
    trips = query.offset((page - 1) * limit).limit(limit).all()
    return paginated_response([t.to_dict() for t in trips], page, limit, total)


@trip_bp.route("/<string:trip_id>", methods=["GET"])
@jwt_required()
@handle_service_errors
def get_trip(trip_id: str):
    """Get full trip detail including stops."""
    trip = _get_trip_or_404(trip_id)
    include_stops = request.args.get("include_stops", "true").lower() == "true"
    return success_response(trip.to_dict(include_stops=include_stops))


@trip_bp.route("", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def start_trip():
    """Start a new trip for a vehicle."""
    claims = get_jwt()
    data = request.get_json(silent=True) or {}

    for field in ("vehicle_id", "start_latitude", "start_longitude"):
        if data.get(field) is None:
            return error_response(f"'{field}' is required", 422)

    trip = TripService.start_trip(
        vehicle_id=data["vehicle_id"],
        start_lat=float(data["start_latitude"]),
        start_lng=float(data["start_longitude"]),
        driver_id=data.get("driver_id"),
        organization_id=claims.get("organization_id"),
        notes=data.get("notes"),
        load_status=data.get("load_status", "empty"),
    )
    return success_response(trip.to_dict(), message="Trip started", code=201)


@trip_bp.route("/<string:trip_id>/load-status", methods=["PUT", "PATCH"])
@jwt_required()
@min_role("driver")
@handle_service_errors
def update_load_status(trip_id: str):
    """Update cargo status between 'loaded' and 'empty'."""
    trip = _get_trip_or_404(trip_id)
    data = request.get_json(silent=True) or {}
    new_status = data.get("load_status")
    if new_status not in ("loaded", "empty"):
        return error_response("load_status must be 'loaded' or 'empty'", 422)

    trip.load_status = new_status
    from app.extensions import db
    db.session.commit()
    return success_response(trip.to_dict(), message=f"Trip cargo status set to {new_status}")


@trip_bp.route("/<string:trip_id>/complete", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def complete_trip(trip_id: str):
    """Complete (end) a trip."""
    data = request.get_json(silent=True) or {}
    if data.get("end_latitude") is None or data.get("end_longitude") is None:
        return error_response("end_latitude and end_longitude are required", 422)

    trip = TripService.complete_trip(
        trip_id=trip_id,
        end_lat=float(data["end_latitude"]),
        end_lng=float(data["end_longitude"]),
        notes=data.get("notes"),
    )
    return success_response(trip.to_dict(include_stops=True), message="Trip completed")


@trip_bp.route("/<string:trip_id>/cancel", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def cancel_trip(trip_id: str):
    """Cancel an in-progress trip."""
    data = request.get_json(silent=True) or {}
    trip = TripService.cancel_trip(trip_id, reason=data.get("reason"))
    return success_response(trip.to_dict(), message="Trip cancelled")


@trip_bp.route("/<string:trip_id>/events", methods=["POST"])
@jwt_required()
@min_role("driver")
@handle_service_errors
def add_event(trip_id: str):
    """Record a discrete trip event (overspeed, harsh-brake, etc.)."""
    data = request.get_json(silent=True) or {}
    event_type = data.get("event_type")
    if not event_type:
        return error_response("event_type is required", 422)
    if event_type not in TRIP_EVENT_TYPES:
        return error_response(
            f"Invalid event_type. Choose from: {', '.join(TRIP_EVENT_TYPES)}", 422
        )

    event = TripService.add_trip_event(
        trip_id=trip_id,
        event_type=event_type,
        lat=data.get("latitude"),
        lng=data.get("longitude"),
        speed_kmh=data.get("speed_kmh"),
        heading=data.get("heading"),
        description=data.get("description"),
    )
    return success_response(event.to_dict(), message="Event recorded", code=201)


@trip_bp.route("/<string:trip_id>/events", methods=["GET"])
@jwt_required()
def list_events(trip_id: str):
    """List all events for a trip."""
    _get_trip_or_404(trip_id)
    events = (
        TripEvent.query
        .filter_by(trip_id=trip_id)
        .order_by(TripEvent.occurred_at)
        .all()
    )
    return success_response([e.to_dict() for e in events])


@trip_bp.route("/<string:trip_id>/stops", methods=["GET"])
@jwt_required()
def list_stops(trip_id: str):
    """List detected stops for a trip."""
    _get_trip_or_404(trip_id)
    stops = Stop.query.filter_by(trip_id=trip_id).order_by(Stop.arrived_at).all()
    return success_response([s.to_dict() for s in stops])


@trip_bp.route("/<string:trip_id>/detect-stops", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def detect_stops(trip_id: str):
    """Run stop detection algorithm for a trip and persist results."""
    stops = TrackingService.detect_stops(trip_id)
    return success_response(stops, message=f"{len(stops)} stop(s) detected")


@trip_bp.route("/<string:trip_id>/playback", methods=["GET"])
@jwt_required()
@handle_service_errors
def trip_playback(trip_id: str):
    """Return the GPS trail for animated route playback."""
    trip = _get_trip_or_404(trip_id)
    trail = TrackingService.get_vehicle_gps_history(
        trip.vehicle_id,
        start_time=trip.start_time,
        end_time=trip.end_time,
        limit=2000,
    )
    return success_response({
        "trip": trip.to_dict(include_stops=True),
        "waypoints": trail,
        "waypoints_count": len(trail),
    })


def _get_trip_or_404(trip_id: str) -> Trip:
    trip = Trip.query.get(trip_id)
    if not trip:
        from flask import abort
        abort(404)
    return trip
