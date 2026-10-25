"""
Unit tests for Trips, Cargo Status (loaded/empty), and Company management.
"""
def test_create_and_list_companies(client, auth_headers):
    # Create company
    res = client.post("/api/v1/companies", headers=auth_headers, json={
        "name": "Mahindra Transport Logistics",
        "contact_person": "Sunil Patil",
        "contact_phone": "+91-98200-99887",
        "gst_number": "27AAAPM1234F1Z9"
    })
    assert res.status_code == 201
    comp_id = res.get_json()["data"]["id"]

    # List companies
    list_res = client.get("/api/v1/companies", headers=auth_headers)
    assert list_res.status_code == 200
    assert any(c["id"] == comp_id for c in list_res.get_json()["data"])


def test_start_trip_with_load_status(client, auth_headers):
    # Fetch existing test vehicle
    veh_res = client.get("/api/v1/vehicles", headers=auth_headers)
    vehicle_id = veh_res.get_json()["data"][0]["id"]

    # Start trip with loaded cargo status
    start_res = client.post("/api/v1/trips", headers=auth_headers, json={
        "vehicle_id": vehicle_id,
        "start_latitude": 19.0760,
        "start_longitude": 72.8777,
        "load_status": "loaded",
        "notes": "Steel coils delivery"
    })
    assert start_res.status_code == 201
    trip = start_res.get_json()["data"]
    assert trip["load_status"] == "loaded"
    assert trip["status"] == "in_progress"

    # Update cargo status to empty
    trip_id = trip["id"]
    status_res = client.put(f"/api/v1/trips/{trip_id}/load-status", headers=auth_headers, json={
        "load_status": "empty"
    })
    assert status_res.status_code == 200
    assert status_res.get_json()["data"]["load_status"] == "empty"
