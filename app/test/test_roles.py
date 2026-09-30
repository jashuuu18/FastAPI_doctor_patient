from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def get_admin_token():
    response = client.post(
        "/auth/login",
        data={
            "username": "admin@example.com",
            "password": "your_admin_password"
        }
    )

    return response.json()["access_token"]


def test_admin_can_create_doctor():
    token = get_admin_token()

    response = client.post(
        "/api/v1/doctors",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Test Doctor",
            "specialization": "Cardiology",
            "email": "testdoctor@example.com",
            "phone": "9876543210"
        }
    )

    assert response.status_code in [200, 201]


def test_without_token_is_rejected():
    response = client.post(
        "/api/v1/doctors",
        json={
            "name": "Unauthorized Doctor",
            "specialization": "Cardiology",
            "email": "unauthorized@example.com",
            "phone": "9876543211"
        }
    )

    assert response.status_code == 401