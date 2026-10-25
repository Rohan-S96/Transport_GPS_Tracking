"""
Alert monitoring, filtering, and acknowledgment endpoints.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.alert import Alert
from app.services.alert_service import AlertService
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.decorators import handle_service_errors

alert_bp = Blueprint("alerts", __name__, url_prefix="/api/v1/alerts")

@alert_bp.route("", methods=["GET"])
@jwt_required(optional=True)
def list_alerts():
    """Retrieve safety alerts with severity and acknowledgment filters."""
    severity = request.args.get("severity")
    status = request.args.get("status")  # unacknowledged | acknowledged
    vehicle_id = request.args.get("vehicle_id")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    query = Alert.query
    if vehicle_id:
        query = query.filter_by(vehicle_id=vehicle_id)
    if severity:
        query = query.filter_by(severity=severity)
    if status == "unacknowledged":
        query = query.filter_by(is_acknowledged=False)
    elif status == "acknowledged":
        query = query.filter_by(is_acknowledged=True)

    query = query.order_by(Alert.created_at.desc())
    total_records = query.count()
    alerts = query.offset((page - 1) * limit).limit(limit).all()

    return paginated_response([a.to_dict() for a in alerts], page, limit, total_records)


@alert_bp.route("/<string:alert_id>/acknowledge", methods=["POST"])
@jwt_required()
@handle_service_errors
def acknowledge_alert(alert_id):
    """Mark an alert incident as reviewed and acknowledged."""
    user_id = get_jwt_identity()
    alert = AlertService.acknowledge_alert(alert_id, user_id)
    return success_response(alert.to_dict(), message="Alert acknowledged successfully")


@alert_bp.route("/<string:alert_id>", methods=["DELETE"])
@jwt_required()
@handle_service_errors
def delete_alert(alert_id):
    """Dismiss and delete an alert."""
    alert = Alert.query.get(alert_id)
    if not alert:
        return error_response("Alert not found", 404)
    from app.extensions import db
    db.session.delete(alert)
    db.session.commit()
    return success_response(message="Alert dismissed")

