"""
Authentication and JWT service — user registration, login, token issuance.
"""
import json
from datetime import datetime, timezone
from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token
from app.extensions import db
from app.models.user import Organization, User, ROLES
from app.models.audit import AuditLog


class AuthService:

    @staticmethod
    def register_user(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        org_name: str | None = None,
        role: str = "fleet_manager",
    ) -> User:
        """
        Register a new user account.
        If org_name is provided and does not exist it will be created.
        """
        if role not in ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of: {', '.join(ROLES)}")

        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            raise ValueError("An account with this email address already exists")

        org = None
        if org_name:
            org = Organization.query.filter_by(name=org_name.strip()).first()
            if not org:
                org = Organization(
                    name=org_name.strip(),
                    contact_email=email,
                )
                db.session.add(org)
                db.session.flush()

        user = User(
            organization_id=org.id if org else None,
            email=email,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role=role,
        )
        user.set_password(password)
        db.session.add(user)

        # Audit log
        log = AuditLog(
            user_id=None,
            organization_id=org.id if org else None,
            action="user_register",
            entity_type="user",
            entity_id=user.id,
            detail=json.dumps({"email": email, "role": role}),
            ip_address=_get_remote_ip(),
        )
        db.session.add(log)
        db.session.commit()
        return user

    @staticmethod
    def authenticate_user(email: str, password: str) -> dict:
        """Validate credentials and return JWT tokens + user data."""
        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is deactivated. Please contact an administrator.")

        user.last_login_at = datetime.now(timezone.utc)

        # Audit login
        log = AuditLog(
            user_id=user.id,
            organization_id=user.organization_id,
            action="user_login",
            entity_type="user",
            entity_id=user.id,
            ip_address=_get_remote_ip(),
            user_agent=_get_user_agent(),
        )
        db.session.add(log)
        db.session.commit()

        additional_claims = {
            "role": user.role,
            "organization_id": user.organization_id,
            "full_name": user.full_name,
        }
        access_token = create_access_token(
            identity=user.id, additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "user": user.to_dict(),
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_remote_ip() -> str | None:
    try:
        return request.remote_addr
    except RuntimeError:
        return None


def _get_user_agent() -> str | None:
    try:
        return request.headers.get("User-Agent", "")[:255]
    except RuntimeError:
        return None
