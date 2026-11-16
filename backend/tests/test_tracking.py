"""
Unit tests for GPS telemetry and distance calculations.
"""
from app.utils.geo_utils import haversine_distance_km

def test_haversine_formula_distance():
    # Mumbai CST to Pune Railway Station (~120 km)
    cst_lat, cst_lng = 18.9401, 72.8354
    pune_lat, pune_lng = 18.5284, 73.8744
    dist = haversine_distance_km(cst_lat, cst_lng, pune_lat, pune_lng)
    assert 110 < dist < 135


def test_telemetry_ingest_and_overspeed_detection(client):
    # Post overspeed coordinate (> 80 km/h) to primary GPS endpoint
    res = client.post("/api/v1/gps/locations", json={
        "device_imei": "111222333444555",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "speed_kmh": 95.5,
        "heading": 120.0,
        "ignition": True
    })
    assert res.status_code == 201
    assert res.get_json()["data"]["alerts_generated"] >= 1


def test_mobile_tracking_by_registration_number(client):
    """Test mobile driver GPS telemetry ingest using only registration number."""
    res = client.post("/api/v1/gps/locations", json={
        "registration_number": "TEST-REG-01",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "speed_kmh": 42.0,
        "heading": 180.0,
        "battery_pct": 88.0,
        "ignition": True
    })
    assert res.status_code == 201
    body = res.get_json()
    assert body["success"] is True
    assert body["data"]["registration_number"] == "TEST-REG-01"


def test_public_vehicle_roster_endpoint(client):
    """Test public vehicle roster used by driver mobile web tracker without auth."""
    res = client.get("/api/v1/vehicles/public-roster")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data) >= 1
    assert any(v["registration_number"] == "TEST-REG-01" for v in data)


def test_gps_connect_and_disconnect_endpoints(client):
    """Test explicit device connect and disconnect endpoints."""
    # 1. Connect
    res = client.post("/api/v1/gps/connect", json={
        "registration_number": "TEST-REG-01"
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["is_online"] is True
    assert data["status"] == "active"

    # 2. Disconnect
    res = client.post("/api/v1/gps/disconnect", json={
        "registration_number": "TEST-REG-01"
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["is_online"] is False
    assert data["status"] == "offline"



