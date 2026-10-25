"""Initial database schema migration for Transport GPS Tracking.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-10-13 13:30:00

"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("contact_email", sa.String(length=120), nullable=False),
        sa.Column("contact_phone", sa.String(length=25), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # 2. Users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("email", sa.String(length=120), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=60), nullable=False),
        sa.Column("last_name", sa.String(length=60), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="manager"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 3. Drivers
    op.create_table(
        "drivers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("first_name", sa.String(length=60), nullable=False),
        sa.Column("last_name", sa.String(length=60), nullable=False),
        sa.Column("license_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column("phone_number", sa.String(length=25), nullable=False),
        sa.Column("safety_score", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="available"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 4. Vehicles
    op.create_table(
        "vehicles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("assigned_driver_id", sa.String(length=36), sa.ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("registration_number", sa.String(length=30), nullable=False, unique=True),
        sa.Column("vin", sa.String(length=50), nullable=True, unique=True),
        sa.Column("make", sa.String(length=60), nullable=False),
        sa.Column("model", sa.String(length=60), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("device_imei", sa.String(length=30), nullable=True, unique=True),
        sa.Column("fuel_type", sa.String(length=20), nullable=False, server_default="diesel"),
        sa.Column("fuel_capacity_litres", sa.Float(), nullable=False, server_default="300.0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("current_odometer_km", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 5. GPS Telemetry
    op.create_table(
        "gps_telemetry",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("vehicle_id", sa.String(length=36), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.Column("speed_kmh", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("heading", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("satellites", sa.Integer(), nullable=True, server_default="8"),
        sa.Column("ignition", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("battery_pct", sa.Float(), nullable=True, server_default="100.0"),
        sa.Column("fuel_level_pct", sa.Float(), nullable=True),
        sa.Column("odometer_km", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("idx_vehicle_recorded_at", "gps_telemetry", ["vehicle_id", "recorded_at"])

    # 6. Geofences
    op.create_table(
        "geofences",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("fence_type", sa.String(length=20), nullable=False, server_default="circle"),
        sa.Column("center_latitude", sa.Float(), nullable=True),
        sa.Column("center_longitude", sa.Float(), nullable=True),
        sa.Column("radius_meters", sa.Float(), nullable=True),
        sa.Column("coordinates_json", sa.Text(), nullable=True),
        sa.Column("alert_on_entry", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("alert_on_exit", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("color_hex", sa.String(length=10), nullable=False, server_default="#3B82F6"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 7. Alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("vehicle_id", sa.String(length=36), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("geofence_id", sa.String(length=36), sa.ForeignKey("geofences.id", ondelete="SET NULL"), nullable=True),
        sa.Column("alert_type", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=15), nullable=False, server_default="warning"),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("is_acknowledged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("acknowledged_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 8. Trips
    op.create_table(
        "trips",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("vehicle_id", sa.String(length=36), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", sa.String(length=36), sa.ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("start_latitude", sa.Float(), nullable=False),
        sa.Column("start_longitude", sa.Float(), nullable=False),
        sa.Column("end_latitude", sa.Float(), nullable=True),
        sa.Column("end_longitude", sa.Float(), nullable=True),
        sa.Column("distance_km", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("duration_minutes", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("max_speed_kmh", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("avg_speed_kmh", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="in_progress"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 9. Maintenance & Fuel Logs
    op.create_table(
        "maintenance_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("vehicle_id", sa.String(length=36), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_type", sa.String(length=80), nullable=False),
        sa.Column("odometer_at_service", sa.Float(), nullable=False),
        sa.Column("cost_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("next_due_odometer", sa.Float(), nullable=True),
        sa.Column("next_due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "fuel_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("vehicle_id", sa.String(length=36), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("litres_filled", sa.Float(), nullable=False),
        sa.Column("total_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("odometer_km", sa.Float(), nullable=False),
        sa.Column("fuel_station", sa.String(length=120), nullable=True),
        sa.Column("filled_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("fuel_logs")
    op.drop_table("maintenance_logs")
    op.drop_table("trips")
    op.drop_table("alerts")
    op.drop_table("geofences")
    op.drop_table("gps_telemetry")
    op.drop_table("vehicles")
    op.drop_table("drivers")
    op.drop_table("users")
    op.drop_table("organizations")
