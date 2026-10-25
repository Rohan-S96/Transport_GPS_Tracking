"""
Report service — Excel and CSV exports using pandas + openpyxl.
Audit-logs every export.
"""
import io
import json
from datetime import datetime, timezone
import pandas as pd
from flask import current_app
from app.extensions import db
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.trip import Trip
from app.models.alert import Alert
from app.models.maintenance import MaintenanceLog, FuelLog
from app.models.audit import ReportExport


class ReportService:

    @staticmethod
    def export_vehicles(format_type: str = "excel", organization_id: str | None = None) -> tuple:
        query = Vehicle.query
        if organization_id:
            query = query.filter_by(organization_id=organization_id)

        rows = []
        for v in query.all():
            driver = v.assigned_driver
            rows.append({
                "Registration": v.registration_number,
                "VIN": v.vin or "",
                "Make": v.make,
                "Model": v.model,
                "Year": v.year or "",
                "Status": v.status,
                "Fuel Type": v.fuel_type,
                "Odometer (km)": round(v.current_odometer_km, 1),
                "Driver": driver.full_name if driver else "Unassigned",
                "Speed Limit (km/h)": v.speed_limit_kmh or "",
                "Created": v.created_at.strftime("%Y-%m-%d") if v.created_at else "",
            })

        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        return ReportService._render(df, format_type, "vehicles_report", organization_id)

    @staticmethod
    def export_trips(format_type: str = "excel", organization_id: str | None = None) -> tuple:
        query = Trip.query
        if organization_id:
            query = query.filter_by(organization_id=organization_id)

        rows = []
        for t in query.order_by(Trip.start_time.desc()).all():
            rows.append({
                "Trip ID": t.id[:8],
                "Vehicle": t.vehicle.registration_number if t.vehicle else "",
                "Driver": t.driver.full_name if t.driver else "",
                "Status": t.status,
                "Start Time": t.start_time.strftime("%Y-%m-%d %H:%M") if t.start_time else "",
                "End Time": t.end_time.strftime("%Y-%m-%d %H:%M") if t.end_time else "",
                "Distance (km)": round(t.distance_km, 2),
                "Duration (min)": round(t.duration_minutes, 1),
                "Max Speed (km/h)": round(t.max_speed_kmh, 1),
                "Avg Speed (km/h)": round(t.avg_speed_kmh, 1),
                "Idle (min)": round(t.idle_minutes, 1),
            })

        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        return ReportService._render(df, format_type, "trips_report", organization_id)

    @staticmethod
    def export_alerts(format_type: str = "excel", organization_id: str | None = None) -> tuple:
        query = Alert.query
        if organization_id:
            query = query.filter_by(organization_id=organization_id)

        rows = []
        for a in query.order_by(Alert.created_at.desc()).all():
            rows.append({
                "Alert Type": a.alert_type,
                "Severity": a.severity,
                "Vehicle": a.vehicle.registration_number if a.vehicle else "",
                "Message": a.message,
                "Speed (km/h)": a.speed_kmh or "",
                "Latitude": a.latitude or "",
                "Longitude": a.longitude or "",
                "Acknowledged": "Yes" if a.is_acknowledged else "No",
                "Created": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "",
            })

        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        return ReportService._render(df, format_type, "alerts_report", organization_id)

    @staticmethod
    def export_drivers(format_type: str = "excel", organization_id: str | None = None) -> tuple:
        query = Driver.query
        if organization_id:
            query = query.filter_by(organization_id=organization_id)

        rows = []
        for d in query.all():
            rows.append({
                "Name": d.full_name,
                "License Number": d.license_number,
                "License Expiry": d.license_expiry.isoformat() if d.license_expiry else "",
                "Phone": d.phone_number,
                "Email": d.email or "",
                "Status": d.status,
                "Safety Score": round(d.safety_score, 1),
            })

        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        return ReportService._render(df, format_type, "drivers_report", organization_id)

    @staticmethod
    def export_fuel(format_type: str = "excel", organization_id: str | None = None) -> tuple:
        query = FuelLog.query
        if organization_id:
            query = query.join(Vehicle).filter(Vehicle.organization_id == organization_id)

        rows = []
        for f in query.order_by(FuelLog.filled_at.desc()).all():
            rows.append({
                "Vehicle": f.vehicle.registration_number if f.vehicle else "",
                "Litres Filled": round(f.litres_filled, 2),
                "Total Cost": float(f.total_cost),
                "Odometer (km)": round(f.odometer_km, 1),
                "Station": f.fuel_station or "",
                "Date": f.filled_at.strftime("%Y-%m-%d %H:%M") if f.filled_at else "",
            })

        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        return ReportService._render(df, format_type, "fuel_report", organization_id)

    # ── Private helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _render(
        df: pd.DataFrame,
        format_type: str,
        prefix: str,
        organization_id: str | None,
    ) -> tuple:
        """Render DataFrame to BytesIO buffer and return (buffer, mimetype, filename)."""
        buf = io.BytesIO()
        fmt = (format_type or "excel").lower()

        if fmt == "csv":
            df.to_csv(buf, index=False)
            mimetype = "text/csv"
            filename = f"{prefix}.csv"
        else:
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Data", index=False)
                # Auto-fit column widths
                ws = writer.sheets["Data"]
                for col in ws.columns:
                    max_len = max((len(str(cell.value or "")) for cell in col), default=0)
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
            mimetype = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            filename = f"{prefix}.xlsx"

        buf.seek(0)

        # Audit log the export
        try:
            log = ReportExport(
                organization_id=organization_id,
                report_type=prefix.split("_")[0],
                format=fmt,
                status="completed",
                row_count=len(df),
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            pass  # Non-critical; don't fail the download

        return buf, mimetype, filename
