"""
Unit tests for authentication endpoints.
"""
def test_login_successful(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "tester@fleetcorp.com",
        "password": "Password123!"
    })
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert "access_token" in json_data["data"]


def test_login_invalid_credentials(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "tester@fleetcorp.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 400
    assert res.get_json()["success"] is False


def test_get_current_user_profile(client, auth_headers):
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["email"] == "tester@fleetcorp.com"
    assert data["role"] == "admin"
