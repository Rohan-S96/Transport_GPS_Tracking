"""
Fleet analytics, KPI summaries, and Excel/CSV data exports.
"""
from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt
from app.models.vehicle import Vehicle
from app.models.alert import Alert
from app.models.trip import Trip
from app.services.report_service import ReportService
from app.utils.decorators import min_role
from app.utils.response_utils import success_response, error_response

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/v1/analytics")

@analytics_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_fleet_summary():
    """Retrieve operational fleet KPI counts and statistics for authenticated organization."""
    claims = get_jwt()
    org_id = claims.get("organization_id")
    role = claims.get("role", "viewer")

    v_query = Vehicle.query
    a_query = Alert.query
    t_query = Trip.query

    if role != "admin" and org_id:
        v_query = v_query.filter_by(organization_id=org_id)
        a_query = a_query.join(Vehicle).filter(Vehicle.organization_id == org_id)
        t_query = t_query.join(Vehicle).filter(Vehicle.organization_id == org_id)

    total_vehicles = v_query.count()
    active_vehicles = v_query.filter_by(status="active").count()
    idle_vehicles = v_query.filter_by(status="idle").count()
    maintenance_vehicles = v_query.filter_by(status="maintenance").count()
    offline_vehicles = total_vehicles - (active_vehicles + idle_vehicles + maintenance_vehicles)

    unacknowledged_alerts = a_query.filter_by(is_acknowledged=False).count()
    total_trips = t_query.count()
    total_odometer = sum([v.current_odometer_km for v in v_query.all()])

    return success_response({
        "fleet": {
            "total_vehicles": total_vehicles,
            "active": active_vehicles,
            "idle": idle_vehicles,
            "maintenance": maintenance_vehicles,
            "offline": max(0, offline_vehicles),
        },
        "alerts": {
            "unacknowledged": unacknowledged_alerts,
        },
        "trips": {
            "total_recorded": total_trips,
        },
        "total_fleet_km": round(total_odometer, 1),
    })


@analytics_bp.route("/export", methods=["GET"])
@min_role("fleet_manager")
def export_data():
    """
    Export fleet records as Excel (.xlsx) or CSV.
    Protected by JWT authentication and requires at least 'fleet_manager' role.
    Streams directly from in-memory BytesIO buffer without persistent disk caching.
    """
    claims = get_jwt()
    org_id = claims.get("organization_id")
    role = claims.get("role", "viewer")

    # Admins can see all if no org_id, other roles are filtered to their tenant org
    filter_org_id = org_id if role != "admin" else None

    export_type = request.args.get("type", "vehicles").lower()  # vehicles | trips | alerts | drivers | fuel
    format_type = request.args.get("format", "excel").lower()   # excel | csv

    try:
        if export_type == "trips":
            buffer, mimetype, filename = ReportService.export_trips(format_type, organization_id=filter_org_id)
        elif export_type == "alerts":
            buffer, mimetype, filename = ReportService.export_alerts(format_type, organization_id=filter_org_id)
        elif export_type == "drivers":
            buffer, mimetype, filename = ReportService.export_drivers(format_type, organization_id=filter_org_id)
        elif export_type == "fuel":
            buffer, mimetype, filename = ReportService.export_fuel(format_type, organization_id=filter_org_id)
        else:
            buffer, mimetype, filename = ReportService.export_vehicles(format_type, organization_id=filter_org_id)

        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return error_response("Export generation failed", 500, details=str(e))
