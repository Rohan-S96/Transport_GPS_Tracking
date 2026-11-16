"""
Unit tests for vehicle fleet management.
"""
def test_list_vehicles(client, auth_headers):
    res = client.get("/api/v1/vehicles", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data) >= 1
    assert data[0]["registration_number"] == "TEST-REG-01"
    assert "is_online" in data[0]
    assert "gps_device" in data[0]


def test_vehicle_online_offline_status_and_filter(client, auth_headers):
    # Connect vehicle to online
    client.post("/api/v1/gps/connect", json={"registration_number": "TEST-REG-01"})
    
    # Query online vehicles
    res_online = client.get("/api/v1/vehicles?status=online", headers=auth_headers)
    assert res_online.status_code == 200
    online_vehicles = res_online.get_json()["data"]
    assert any(v["registration_number"] == "TEST-REG-01" and v["is_online"] is True for v in online_vehicles)

    # Disconnect vehicle to offline
    client.post("/api/v1/gps/disconnect", json={"registration_number": "TEST-REG-01"})

    # Query offline vehicles
    res_offline = client.get("/api/v1/vehicles?status=offline", headers=auth_headers)
    assert res_offline.status_code == 200
    offline_vehicles = res_offline.get_json()["data"]
    assert any(v["registration_number"] == "TEST-REG-01" and v["is_online"] is False for v in offline_vehicles)


def test_create_vehicle_duplicate_error(client, auth_headers):
    res = client.post("/api/v1/vehicles", headers=auth_headers, json={
        "registration_number": "TEST-REG-01",
        "make": "Volvo",
        "model": "FH16"
    })
    assert res.status_code in (400, 409)
    assert "already exists" in res.get_json()["error"]

