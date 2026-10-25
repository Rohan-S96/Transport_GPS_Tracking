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

