"""Extended database schema migration: stops, trip_events, gps_devices, companies, company_locations, audit_logs, load_status.

Revision ID: 002_extended_schema
Revises: 001_initial_schema
Create Date: 2026-10-13 14:35:00

"""
from alembic import op
import sqlalchemy as sa

revision = "002_extended_schema"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None

def upgrade():
    # 1. Add load_status column to trips
    with op.batch_alter_table("trips") as batch_op:
        batch_op.add_column(
            sa.Column("load_status", sa.String(length=20), nullable=True, server_default="empty")
        )

    # 2. GPS Devices
    op.create_table(
        "gps_devices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("vehicle_id", sa.String(length=36), sa.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("imei", sa.String(length=30), nullable=False, unique=True),
        sa.Column("serial_number", sa.String(length=60), nullable=True),
        sa.Column("manufacturer", sa.String(length=60), nullable=True),
        sa.Column("model", sa.String(length=60), nullable=True),
        sa.Column("firmware_version", sa.String(length=30), nullable=True),
        sa.Column("sim_iccid", sa.String(length=30), nullable=True),
        sa.Column("sim_phone", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("installed_at", sa.Date(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_gps_devices_imei", "gps_devices", ["imei"])

    # 3. Companies
    op.create_table(
        "companies",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("contact_person", sa.String(length=100), nullable=True),
        sa.Column("contact_email", sa.String(length=120), nullable=True),
        sa.Column("contact_phone", sa.String(length=25), nullable=True),
        sa.Column("gst_number", sa.String(length=30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_companies_org", "companies", ["organization_id"])

    # 4. Company Locations
    op.create_table(
        "company_locations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("company_id", sa.String(length=36), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("geofence_id", sa.String(length=36), sa.ForeignKey("geofences.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=80), nullable=True),
        sa.Column("state", sa.String(length=80), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("location_type", sa.String(length=30), nullable=False, server_default="warehouse"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_company_locations_comp", "company_locations", ["company_id"])

    # 5. Trip Stops
    op.create_table(
        "stops",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_id", sa.String(length=36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("arrived_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("departed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_idle", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_stops_trip", "stops", ["trip_id"])

    # 6. Trip Events
    op.create_table(
        "trip_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("trip_id", sa.String(length=36), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("speed_kmh", sa.Float(), nullable=True),
        sa.Column("heading", sa.Float(), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_trip_events_trip", "trip_events", ["trip_id"])

    # 7. Report Exports
    op.create_table(
        "report_exports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("requested_by", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("report_type", sa.String(length=30), nullable=False),
        sa.Column("format", sa.String(length=10), nullable=False, server_default="excel"),
        sa.Column("status", sa.String(length=15), nullable=False, server_default="completed"),
        sa.Column("filter_params", sa.Text(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Audit Logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("organization_id", sa.String(length=36), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=True),
        sa.Column("entity_id", sa.String(length=36), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_audit_logs_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_created", "audit_logs", ["created_at"])


def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("report_exports")
    op.drop_table("trip_events")
    op.drop_table("stops")
    op.drop_table("company_locations")
    op.drop_table("companies")
    op.drop_table("gps_devices")
    with op.batch_alter_table("trips") as batch_op:
        batch_op.drop_column("load_status")
