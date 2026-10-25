"""
Unit tests for vehicle fleet management.
"""
def test_list_vehicles(client, auth_headers):
    res = client.get("/api/v1/vehicles", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data) >= 1
    assert data[0]["registration_number"] == "TEST-REG-01"


def test_create_vehicle_duplicate_error(client, auth_headers):
    res = client.post("/api/v1/vehicles", headers=auth_headers, json={
        "registration_number": "TEST-REG-01",
        "make": "Volvo",
        "model": "FH16"
    })
    assert res.status_code in (400, 409)
    assert "already exists" in res.get_json()["error"]

