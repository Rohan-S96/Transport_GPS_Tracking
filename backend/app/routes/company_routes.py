"""
Company and CompanyLocation CRUD routes.
Prefix: /api/v1/companies
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
from app.extensions import db
from app.models.company import Company, CompanyLocation
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.decorators import handle_service_errors, min_role

company_bp = Blueprint("companies", __name__, url_prefix="/api/v1/companies")


@company_bp.route("", methods=["GET"])
@jwt_required()
def list_companies():
    """List companies for caller's org."""
    claims = get_jwt()
    org_id = claims.get("organization_id")
    role = claims.get("role", "viewer")
    search = request.args.get("search", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 20))))

    query = Company.query
    if role != "admin" and org_id:
        query = query.filter_by(organization_id=org_id)
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Company.name.ilike(like),
                Company.contact_person.ilike(like),
                Company.contact_email.ilike(like),
            )
        )

    query = query.order_by(Company.name.asc())
    total = query.count()
    companies = query.offset((page - 1) * limit).limit(limit).all()
    return paginated_response([c.to_dict(include_locations=True) for c in companies], page, limit, total)


@company_bp.route("/<string:company_id>", methods=["GET"])
@jwt_required()
def get_company(company_id: str):
    """Get single company details with locations."""
    company = _get_company_or_404(company_id)
    return success_response(company.to_dict(include_locations=True))


@company_bp.route("", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def create_company():
    """Register a new customer/freight client company."""
    claims = get_jwt()
    data = request.get_json(silent=True) or {}

    if not data.get("name"):
        return error_response("'name' is required", 422)

    company = Company(
        organization_id=claims.get("organization_id"),
        name=data["name"].strip(),
        contact_person=data.get("contact_person"),
        contact_email=data.get("contact_email"),
        contact_phone=data.get("contact_phone"),
        gst_number=data.get("gst_number"),
        notes=data.get("notes"),
    )
    db.session.add(company)
    db.session.commit()
    return success_response(company.to_dict(include_locations=True), message="Company created", code=201)


@company_bp.route("/<string:company_id>", methods=["PUT"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def update_company(company_id: str):
    """Update company details."""
    company = _get_company_or_404(company_id)
    data = request.get_json(silent=True) or {}

    for field in ("name", "contact_person", "contact_email", "contact_phone", "gst_number", "notes", "is_active"):
        if field in data:
            setattr(company, field, data[field])

    db.session.commit()
    return success_response(company.to_dict(include_locations=True), message="Company updated")


@company_bp.route("/<string:company_id>", methods=["DELETE"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def delete_company(company_id: str):
    """Delete a company and its locations."""
    company = _get_company_or_404(company_id)
    db.session.delete(company)
    db.session.commit()
    return success_response(message="Company deleted successfully")


@company_bp.route("/<string:company_id>/locations", methods=["POST"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def add_location(company_id: str):
    """Add a pickup/delivery depot location for a company."""
    company = _get_company_or_404(company_id)
    data = request.get_json(silent=True) or {}

    if not data.get("name"):
        return error_response("'name' is required", 422)

    loc = CompanyLocation(
        company_id=company.id,
        geofence_id=data.get("geofence_id"),
        name=data["name"].strip(),
        address=data.get("address"),
        city=data.get("city"),
        state=data.get("state"),
        postal_code=data.get("postal_code"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        location_type=data.get("location_type", "warehouse"),
    )
    db.session.add(loc)
    db.session.commit()
    return success_response(loc.to_dict(), message="Location added", code=201)


@company_bp.route("/<string:company_id>/locations/<string:location_id>", methods=["DELETE"])
@jwt_required()
@min_role("fleet_manager")
@handle_service_errors
def delete_location(company_id: str, location_id: str):
    """Delete a company location."""
    _get_company_or_404(company_id)
    loc = CompanyLocation.query.filter_by(id=location_id, company_id=company_id).first()
    if not loc:
        from flask import abort
        abort(404)

    db.session.delete(loc)
    db.session.commit()
    return success_response(message="Location deleted")


def _get_company_or_404(company_id: str) -> Company:
    company = Company.query.get(company_id)
    if not company:
        from flask import abort
        abort(404)
    return company
