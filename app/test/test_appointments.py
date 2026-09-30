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


def test_create_appointment():
    token = get_admin_token()

    response = client.post(
        "/api/v1/appointments",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "doctor_id": 1,
            "patient_id": 1,
            "appointment_date": "2026-10-01T10:00:00",
            "status": "scheduled"
        }
    )

    assert response.status_code in [200, 201]