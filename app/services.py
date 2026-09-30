from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Doctor


def get_active_doctor(
    db: Session,
    doctor_id: int
):

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    if not doctor.is_active:

        raise HTTPException(
            status_code=400,
            detail="Doctor is inactive"
        )

    return doctor