from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Patient, Doctor

from app.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientPatch,
    PatientResponse,
)

from app.dependencies import (
    get_current_user,
    admin_required,
)


# =========================
# ROUTER
# =========================

router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Patients"],

    responses={
        404: {
            "description": "Patient or doctor not found"
        },
        403: {
            "description": "Access denied"
        }
    }
)


# =========================
# CREATE PATIENT
# =========================

@router.post(
    "/",
    response_model=PatientResponse,
    summary="Create patient",
    description="Create a patient and assign the patient to an active doctor."
)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    doctor = db.query(Doctor).filter(
        Doctor.id == patient_data.doctor_id
    ).first()

    if not doctor:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    if not doctor.is_active:

        raise HTTPException(
            status_code=400,
            detail="Cannot assign patient to inactive doctor"
        )

    patient = Patient(
        name=patient_data.name,
        age=patient_data.age,
        phone=patient_data.phone,
        doctor_id=patient_data.doctor_id
    )

    db.add(patient)

    db.commit()

    db.refresh(patient)

    return patient


# =========================
# GET ALL PATIENTS
# =========================

@router.get(
    "/",
    response_model=list[PatientResponse],
    summary="Get patients",
    description="Get patients. Doctors can view their assigned patients."
)
def get_patients(
    age_gt: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    query = db.query(Patient)

    # Doctor can only see assigned patients
    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not doctor:

            return []

        query = query.filter(
            Patient.doctor_id == doctor.id
        )

    if age_gt is not None:

        query = query.filter(
            Patient.age > age_gt
        )

    return query.all()


# =========================
# GET PATIENT BY ID
# =========================

@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get patient by ID"
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()

    if not patient:

        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    # Doctor can only view assigned patient
    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not doctor or patient.doctor_id != doctor.id:

            raise HTTPException(
                status_code=403,
                detail="You can only view your assigned patients"
            )

    return patient


# =========================
# UPDATE PATIENT
# =========================

@router.put(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update patient",
    description="Update patient information."
)
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()

    if not patient:

        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    # Doctor can update only assigned patient
    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not doctor or patient.doctor_id != doctor.id:

            raise HTTPException(
                status_code=403,
                detail="You can only update your assigned patients"
            )

    doctor = db.query(Doctor).filter(
        Doctor.id == patient_data.doctor_id
    ).first()

    if not doctor:

        raise HTTPException(
            status_code=404,
            detail="Doctor not found"
        )

    if not doctor.is_active:

        raise HTTPException(
            status_code=400,
            detail="Cannot assign patient to inactive doctor"
        )

    patient.name = patient_data.name
    patient.age = patient_data.age
    patient.phone = patient_data.phone
    patient.doctor_id = patient_data.doctor_id

    db.commit()

    db.refresh(patient)

    return patient


# =========================
# PATCH PATIENT
# =========================

@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Partially update patient"
)
def patch_patient(
    patient_id: int,
    patient_data: PatientPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()

    if not patient:

        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    # Doctor restriction
    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not doctor or patient.doctor_id != doctor.id:

            raise HTTPException(
                status_code=403,
                detail="You can only update your assigned patients"
            )

    data = patient_data.model_dump(
        exclude_unset=True
    )

    if "doctor_id" in data:

        doctor = db.query(Doctor).filter(
            Doctor.id == data["doctor_id"]
        ).first()

        if not doctor:

            raise HTTPException(
                status_code=404,
                detail="Doctor not found"
            )

        if not doctor.is_active:

            raise HTTPException(
                status_code=400,
                detail="Cannot assign patient to inactive doctor"
            )

    for key, value in data.items():

        setattr(
            patient,
            key,
            value
        )

    db.commit()

    db.refresh(patient)

    return patient


# =========================
# DELETE PATIENT
# =========================

@router.delete(
    "/{patient_id}",
    summary="Delete patient",
    description="Only administrators can delete patients."
)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    patient = db.query(Patient).filter(
        Patient.id == patient_id
    ).first()

    if not patient:

        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    db.delete(patient)

    db.commit()

    return {
        "message": "Patient deleted successfully"
    }