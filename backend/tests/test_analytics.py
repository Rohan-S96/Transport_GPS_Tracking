"""
Unit tests for analytics summary and protected Excel/CSV report exports.
"""
def test_get_fleet_summary_authenticated(client, auth_headers):
    res = client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert "fleet" in data
    assert "total_vehicles" in data["fleet"]
    assert "alerts" in data
    assert "trips" in data


def test_export_unauthenticated_fails(client):
    res = client.get("/api/v1/analytics/export?type=vehicles&format=csv")
    # Unauthenticated must be blocked with 401
    assert res.status_code == 401


def test_export_vehicles_csv_as_admin(client, auth_headers):
    res = client.get("/api/v1/analytics/export?type=vehicles&format=csv", headers=auth_headers)
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    assert "Registration" in res.get_data(as_text=True)


def test_export_trips_excel_as_admin(client, auth_headers):
    res = client.get("/api/v1/analytics/export?type=trips&format=excel", headers=auth_headers)
    assert res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res.content_type
    assert len(res.data) > 0
