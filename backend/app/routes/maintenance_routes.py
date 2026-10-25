"""
Vehicle maintenance schedules and fuel logging routes.
"""
from datetime import datetime, date, timezone
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models.maintenance import MaintenanceLog, FuelLog
from app.models.vehicle import Vehicle
from app.utils.response_utils import success_response, error_response
from app.utils.decorators import handle_service_errors, min_role

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/api/v1/maintenance")


@maintenance_bp.route("/logs", methods=["GET"])
@jwt_required(optional=True)
def list_maintenance_logs():
    """List servicing records with optional vehicle_id filter."""
    vehicle_id = request.args.get("vehicle_id")
    query = MaintenanceLog.query
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    logs = query.order_by(MaintenanceLog.service_date.desc()).all()
    return success_response([l.to_dict() for l in logs])


@maintenance_bp.route("/logs", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def create_maintenance_log():
    """Create a new maintenance service record."""
    data = request.get_json(silent=True) or {}
    for f in ("vehicle_id", "service_type", "odometer_at_service"):
        if data.get(f) is None:
            return error_response(f"'{f}' is required", 422)

    vehicle = Vehicle.query.get(data["vehicle_id"])
    if not vehicle:
        return error_response("Vehicle not found", 404)

    service_date = date.today()
    if data.get("service_date"):
        try:
            service_date = date.fromisoformat(data["service_date"])
        except ValueError:
            return error_response("Invalid service_date format (YYYY-MM-DD required)", 422)

    log = MaintenanceLog(
        vehicle_id=data["vehicle_id"],
        service_type=data["service_type"].strip(),
        odometer_at_service=float(data["odometer_at_service"]),
        cost_amount=float(data.get("cost_amount", 0.0)),
        service_date=service_date,
        next_due_odometer=float(data["next_due_odometer"]) if data.get("next_due_odometer") else None,
        notes=data.get("notes"),
    )
    db.session.add(log)
    db.session.commit()
    return success_response(log.to_dict(), message="Maintenance record logged", code=201)


@maintenance_bp.route("/logs/<string:log_id>", methods=["DELETE"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def delete_maintenance_log(log_id: str):
    """Delete a maintenance log."""
    log = MaintenanceLog.query.get(log_id)
    if not log:
        return error_response("Maintenance log not found", 404)
    db.session.delete(log)
    db.session.commit()
    return success_response(message="Maintenance log deleted")


@maintenance_bp.route("/fuel", methods=["GET"])
@jwt_required(optional=True)
def list_fuel_logs():
    """List refueling logs with optional vehicle_id filter."""
    vehicle_id = request.args.get("vehicle_id")
    query = FuelLog.query
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    logs = query.order_by(FuelLog.filled_at.desc()).all()
    return success_response([l.to_dict() for l in logs])


@maintenance_bp.route("/fuel", methods=["POST"])
@jwt_required()
@min_role("driver")
@handle_service_errors
def create_fuel_log():
    """Record a refueling transaction."""
    data = request.get_json(silent=True) or {}
    for f in ("vehicle_id", "litres_filled", "total_cost", "odometer_km"):
        if data.get(f) is None:
            return error_response(f"'{f}' is required", 422)

    vehicle = Vehicle.query.get(data["vehicle_id"])
    if not vehicle:
        return error_response("Vehicle not found", 404)

    log = FuelLog(
        vehicle_id=data["vehicle_id"],
        litres_filled=float(data["litres_filled"]),
        total_cost=float(data["total_cost"]),
        odometer_km=float(data["odometer_km"]),
        fuel_station=data.get("fuel_station"),
    )
    db.session.add(log)
    db.session.commit()
    return success_response(log.to_dict(), message="Fuel transaction recorded", code=201)


@maintenance_bp.route("/fuel/<string:fuel_id>", methods=["DELETE"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def delete_fuel_log(fuel_id: str):
    """Delete a fuel log."""
    log = FuelLog.query.get(fuel_id)
    if not log:
        return error_response("Fuel log not found", 404)
    db.session.delete(log)
    db.session.commit()
    return success_response(message="Fuel log deleted")
