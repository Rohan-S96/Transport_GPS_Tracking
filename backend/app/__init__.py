"""
Application factory for the Transport GPS Tracking REST API.
"""
import os
from flask import Flask, jsonify
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors

def create_app(config_name=None):
    """Create and configure an instance of the Flask application."""
    if config_name is None:
        config_name = os.getenv("APP_ENV", os.getenv("FLASK_ENV", "development"))

    app = Flask(__name__)
    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)
    if hasattr(config_class, "init_app"):
        config_class.init_app(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Configure CORS for Vercel deployed frontend and local dev
    allowed_origins = app.config.get("CORS_ORIGINS", ["*"])
    cors_origins = "*" if (len(allowed_origins) == 1 and allowed_origins[0] == "*") else allowed_origins
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
    )

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    # Register CLI commands
    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed initial database records."""
        from app.utils.seed_data import seed_database
        seed_database()


    # Global Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": "Endpoint or resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"success": False, "error": "Method not allowed"}), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({"success": False, "error": "Internal server error", "message": str(error)}), 500

    # JWT Error Handlers
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({"success": False, "error": "Missing Authorization Header", "code": 401}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return jsonify({"success": False, "error": "Invalid token signature", "code": 401}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "error": "Token has expired", "code": 401}), 401

    return app
