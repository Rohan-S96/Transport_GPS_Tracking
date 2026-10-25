"""
Application configuration classes supporting Development, Testing, and Production.

Environment variable reference:
  DATABASE_URL          - PostgreSQL connection string (Supabase format supported)
  SECRET_KEY            - Flask session signing secret (min 32 chars in prod)
  JWT_SECRET_KEY        - JWT token signing key (min 32 chars in prod)
  CORS_ALLOWED_ORIGINS  - Comma-separated list of allowed CORS origins
  OFFLINE_TRUCK_MINUTES - Minutes of silence before truck is flagged offline (default 10)
  DEMO_GPS_MODE         - Enable synthetic GPS demo data; "true" only in dev/staging
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _fix_db_url(url: str) -> str:
    """
    Normalize PostgreSQL URL for SQLAlchemy and the psycopg2 driver.
    Handles Supabase / Heroku postgres:// and postgresql:// schemes,
    ensuring 'postgresql+psycopg2://' is used with the psycopg driver.
    """
    if not url:
        return "sqlite:///transport_gps_dev.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


class Config:
    """Base configuration shared across all environments."""

    # ── Flask ─────────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-CHANGE-in-prod-01234567890abcdef")
    JSON_SORT_KEYS = False

    # ── Database (Supabase PostgreSQL with psycopg2) ──────────────────────────
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = _fix_db_url(
        os.getenv("DATABASE_URL", "sqlite:///transport_gps_dev.db")
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "20")),
    }

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-insecure-jwt-CHANGE-in-prod-0987654321abcdef")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "120"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "30"))
    )
    JWT_ERROR_MESSAGE_KEY = "error"
    JWT_TOKEN_LOCATION = ["headers"]

    # ── CORS ──────────────────────────────────────────────────────────────────
    _raw_cors = os.getenv("CORS_ORIGINS", os.getenv("CORS_ALLOWED_ORIGINS", "*"))
    CORS_ORIGINS = [o.strip() for o in _raw_cors.split(",") if o.strip()]

    # ── Fleet / Tracking settings ─────────────────────────────────────────────
    SPEED_LIMIT_KMH = float(os.getenv("DEFAULT_SPEED_LIMIT_KMH", "80.0"))
    GEOFENCE_ALERT_COOLDOWN_MINUTES = int(os.getenv("GEOFENCE_ALERT_COOLDOWN_MINUTES", "5"))

    # Vehicle offline detection timeout
    GPS_OFFLINE_TIMEOUT_SECONDS = int(
        os.getenv("GPS_OFFLINE_TIMEOUT_SECONDS", str(int(os.getenv("OFFLINE_TRUCK_MINUTES", "10")) * 60))
    )
    OFFLINE_TRUCK_MINUTES = max(1, GPS_OFFLINE_TIMEOUT_SECONDS // 60)

    # Stop detection parameters
    STOP_MINIMUM_DURATION_SECONDS = int(
        os.getenv("STOP_MINIMUM_DURATION_SECONDS", os.getenv("STOP_MIN_SECONDS", "120"))
    )
    STOP_MIN_SECONDS = STOP_MINIMUM_DURATION_SECONDS
    STOP_RADIUS_METERS = float(os.getenv("STOP_RADIUS_METERS", "50.0"))
    STOP_MAX_SPEED_KMH = float(os.getenv("STOP_MAX_SPEED_KMH", "3.0"))

    # Report audit retention in hours
    REPORT_RETENTION_HOURS = int(os.getenv("REPORT_RETENTION_HOURS", "168"))

    # GPS Demo Simulation Mode (must be explicitly enabled in non-prod envs)
    GPS_DEMO_MODE = os.getenv("GPS_DEMO_MODE", os.getenv("DEMO_GPS_MODE", "false")).lower() == "true"
    DEMO_GPS_MODE = GPS_DEMO_MODE


class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"
    # SQLite falls back automatically; silence pool options for SQLite
    @classmethod
    def init_app(cls, app):
        if "sqlite" in (cls.SQLALCHEMY_DATABASE_URI or ""):
            app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}


class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"
    # Ensure production GPS demo mode is unconditionally false
    GPS_DEMO_MODE = False
    DEMO_GPS_MODE = False

    @classmethod
    def init_app(cls, app):
        secret = os.getenv("SECRET_KEY", "")
        jwt_secret = os.getenv("JWT_SECRET_KEY", "")
        db_url = os.getenv("DATABASE_URL", "")
        warnings = []
        if "insecure" in secret or len(secret) < 32:
            warnings.append("SECRET_KEY is insecure or too short (min 32 chars recommended)")
        if "insecure" in jwt_secret or len(jwt_secret) < 32:
            warnings.append("JWT_SECRET_KEY is insecure or too short (min 32 chars recommended)")
        if not db_url or "sqlite" in db_url:
            warnings.append("DATABASE_URL is not set or is using SQLite instead of PostgreSQL")
        for w in warnings:
            app.logger.warning(f"[PRODUCTION CONFIG] {w} — please configure in deployment environment variables.")


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    GPS_DEMO_MODE = False
    DEMO_GPS_MODE = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
