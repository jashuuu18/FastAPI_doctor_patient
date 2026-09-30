from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Doctor, Patient

from app.schemas import (
    DoctorCreate,
    DoctorUpdate,
    DoctorPatch,
    DoctorResponse,
)

from app.dependencies import (
    get_current_user,
    admin_required,
)


# =========================
# ROUTER
# =========================

router = APIRouter(
    prefix="/api/v1/doctors",
    tags=["Doctors"],

    responses={
        404: {
            "description": "Doctor not found"
        },
        403: {
            "description": "Admin access required"
        }
    }
)


# =========================
# CREATE DOCTOR
# =========================

@router.post(
    "/",
    response_model=DoctorResponse,
    summary="Create a doctor",
    description="Create a new doctor. Only administrators can create doctors."
)
def create_doctor(
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    existing_doctor = db.query(Doctor).filter(
        Doctor.email == doctor_data.email
    ).first()

    if existing_doctor:

        raise HTTPException(
            status_code=400,
            detail="Doctor email already exists"
        )

    doctor = Doctor(
        name=doctor_data.name,
        email=doctor_data.email,
        specialization=doctor_data.specialization,
        phone=doctor_data.phone,
        is_active=True
    )

    db.add(doctor)

    db.commit()

    db.refresh(doctor)

    return doctor


# =========================
# GET ALL DOCTORS
# =========================

@router.get(
    "/",
    response_model=list[DoctorResponse],
    summary="Get doctors",
    description="Get all active doctors."
)
def get_doctors(
    specialization: str | None = None,
    is_active: bool | None = True,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    query = db.query(Doctor)

    if specialization:

        query = query.filter(
            Doctor.specialization == specialization
        )

    if is_active is not None:

        query = query.filter(
            Doctor.is_active == is_active
        )

    return query.all()


# =========================
# GET DOCTOR BY ID
# =========================

@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Get doctor by ID",
    description="Get a doctor using the doctor ID."
)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    return doctor


# =========================
# GET DOCTOR PATIENTS
# =========================

@router.get(
    "/{doctor_id}/patients",
    summary="Get doctor's patients",
    description="Get all patients assigned to a doctor."
)
def get_doctor_patients(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    patients = db.query(Patient).filter(
        Patient.doctor_id == doctor_id
    ).all()

    return patients


# =========================
# UPDATE DOCTOR
# =========================

@router.put(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Update doctor",
    description="Update all doctor information. Admin only."
)
def update_doctor(
    doctor_id: int,
    doctor_data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    duplicate = db.query(Doctor).filter(
        Doctor.email == doctor_data.email,
        Doctor.id != doctor_id
    ).first()

    if duplicate:

        raise HTTPException(
            status_code=400,
            detail="Doctor email already exists"
        )

    doctor.name = doctor_data.name
    doctor.email = doctor_data.email
    doctor.specialization = doctor_data.specialization
    doctor.phone = doctor_data.phone

    db.commit()

    db.refresh(doctor)

    return doctor


# =========================
# PATCH DOCTOR
# =========================

@router.patch(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Partially update doctor",
    description="Update selected doctor fields. Admin only."
)
def patch_doctor(
    doctor_id: int,
    doctor_data: DoctorPatch,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    data = doctor_data.model_dump(
        exclude_unset=True
    )

    if "email" in data:

        duplicate = db.query(Doctor).filter(
            Doctor.email == data["email"],
            Doctor.id != doctor_id
        ).first()

        if duplicate:

            raise HTTPException(
                status_code=400,
                detail="Doctor email already exists"
            )

    for key, value in data.items():

        setattr(
            doctor,
            key,
            value
        )

    db.commit()

    db.refresh(doctor)

    return doctor


# =========================
# DELETE DOCTOR
# =========================

@router.delete(
    "/{doctor_id}",
    summary="Delete doctor",
    description="Soft delete a doctor by setting is_active to false."
)
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == doctor_id
    ).first()

    if not doctor:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    doctor.is_active = False

    db.commit()

    return {
        "message": "Doctor deleted successfully"
    }