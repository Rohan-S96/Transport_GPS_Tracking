"""
Pytest configuration and test client fixtures.
"""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User, Organization
from app.models.vehicle import Vehicle
from app.models.gps_device import GPSDevice

@pytest.fixture
def app():
    """Create test application configured for in-memory SQLite."""
    application = create_app("testing")
    with application.app_context():
        db.create_all()
        # Seed test organization and user
        org = Organization(name="Test Fleet Corp", contact_email="test@fleetcorp.com")
        db.session.add(org)
        db.session.flush()

        user = User(
            organization_id=org.id,
            email="tester@fleetcorp.com",
            first_name="Test",
            last_name="User",
            role="admin"
        )
        user.set_password("Password123!")
        db.session.add(user)

        vehicle = Vehicle(
            organization_id=org.id,
            registration_number="TEST-REG-01",
            make="Volvo",
            model="FH16",
            status="active"
        )
        db.session.add(vehicle)
        db.session.flush()

        device = GPSDevice(
            vehicle_id=vehicle.id,
            imei="111222333444555",
            model="Teltonika FMB920"
        )
        db.session.add(device)
        db.session.commit()

        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Helper fixture to obtain JWT Bearer header."""
    res = client.post("/api/v1/auth/login", json={
        "email": "tester@fleetcorp.com",
        "password": "Password123!"
    })
    token = res.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
