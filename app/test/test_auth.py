from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_login_success():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin@example.com",
            "password": "admin123"
        }
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password():
    response = client.post(
        "/auth/login",
        json={
            "username": "admin@example.com",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401