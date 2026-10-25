"""
Health and readiness endpoints for Railway monitoring probes.

  GET /api/v1/health  — liveness probe (always 200 if process is running)
  GET /api/v1/ready   — readiness probe (200 only if database is reachable)
"""
import time
from flask import Blueprint, current_app
from sqlalchemy import text
from app.extensions import db
from app.utils.response_utils import success_response, error_response

health_bp = Blueprint("health", __name__, url_prefix="/api/v1")

_START_TIME = time.time()


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Liveness probe — process is alive."""
    uptime_seconds = round(time.time() - _START_TIME)
    return success_response({
        "status": "ok",
        "service": "Transport GPS Tracking API",
        "version": "1.0.0",
        "uptime_seconds": uptime_seconds,
        "demo_gps_mode": current_app.config.get("DEMO_GPS_MODE", False),
    }, message="Service is running")


@health_bp.route("/ready", methods=["GET"])
def readiness_check():
    """Readiness probe — database connectivity verified."""
    db_status = "ok"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"
        return error_response("Database is not ready", 503, details=db_status)

    return success_response({
        "status": "ready",
        "database": db_status,
    }, message="Service is ready to accept traffic")
