"""
Blueprint registration hub.
"""
from flask import Flask
from app.routes.health_routes import health_bp
from app.routes.auth_routes import auth_bp
from app.routes.vehicle_routes import vehicle_bp
from app.routes.tracking_routes import tracking_bp
from app.routes.geofence_routes import geofence_bp
from app.routes.alert_routes import alert_bp
from app.routes.driver_routes import driver_bp
from app.routes.trip_routes import trip_bp
from app.routes.maintenance_routes import maintenance_bp
from app.routes.analytics_routes import analytics_bp
from app.routes.company_routes import company_bp
from app.routes.user_routes import user_bp

def register_blueprints(app: Flask):
    """Register all REST API blueprints with the Flask application."""
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(vehicle_bp)
    app.register_blueprint(tracking_bp)
    app.register_blueprint(geofence_bp)
    app.register_blueprint(alert_bp)
    app.register_blueprint(driver_bp)
    app.register_blueprint(trip_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(user_bp)
