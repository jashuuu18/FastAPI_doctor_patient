from pydantic import ValidationError
import pytest

from app.schemas import DoctorCreate


def test_invalid_phone():

    with pytest.raises(ValidationError):

        DoctorCreate(
            name="Test Doctor",
            specialization="Cardiology",
            email="doctor@example.com",
            phone="123"
        )