"""
Standardized JSON response envelope utilities.
"""
from datetime import datetime, timezone
from flask import jsonify

def success_response(data=None, message="Success", code=200):
    """Generate consistent success JSON response."""
    payload = {
        "success": True,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if data is not None:
        payload["data"] = data
    return jsonify(payload), code


def paginated_response(data: list, page: int, limit: int, total_records: int, code=200):
    """Generate paginated data response."""
    total_pages = (total_records + limit - 1) // limit if limit > 0 else 1
    return jsonify({
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total_records,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), code


def error_response(message="An error occurred", code=400, details=None):
    """Generate standardized error JSON response."""
    payload = {
        "success": False,
        "error": message,
        "code": code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if details:
        payload["details"] = details
    return jsonify(payload), code
