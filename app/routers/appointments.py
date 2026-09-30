from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Appointment,
    Doctor,
    Patient,
)

from app.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
)

from app.dependencies import (
    get_current_user,
    admin_required,
)


# =========================
# ROUTER
# =========================

router = APIRouter(
    prefix="/api/v1/appointments",
    tags=["Appointments"],

    responses={
        400: {
            "description": "Invalid appointment or overlapping appointment"
        },
        404: {
            "description": "Doctor, patient or appointment not found"
        }
    }
)


# =========================
# CREATE APPOINTMENT
# =========================

@router.post(
    "/",
    response_model=AppointmentResponse,
    summary="Create appointment",
    description="Create an appointment between a doctor and patient."
)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # Check doctor
    doctor = db.query(Doctor).filter(
        Doctor.id == appointment_data.doctor_id
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

    # Check patient
    patient = db.query(Patient).filter(
        Patient.id == appointment_data.patient_id
    ).first()

    if not patient:

        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    # Check patient belongs to doctor
    if patient.doctor_id != doctor.id:

        raise HTTPException(
            status_code=400,
            detail="Patient is not assigned to this doctor"
        )

    # Check overlapping appointment
    existing_appointment = db.query(Appointment).filter(
        Appointment.doctor_id == appointment_data.doctor_id,
        Appointment.appointment_date == appointment_data.appointment_date,
        Appointment.status != "cancelled"
    ).first()

    if existing_appointment:

        raise HTTPException(
            status_code=400,
            detail="Doctor already has an appointment at this time"
        )

    appointment = Appointment(
        doctor_id=appointment_data.doctor_id,
        patient_id=appointment_data.patient_id,
        appointment_date=appointment_data.appointment_date,
        status=appointment_data.status
    )

    db.add(appointment)

    db.commit()

    db.refresh(appointment)

    return appointment


# =========================
# GET ALL APPOINTMENTS
# =========================

@router.get(
    "/",
    response_model=list[AppointmentResponse],
    summary="Get appointments"
)
def get_appointments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    query = db.query(Appointment)

    # Doctor sees only appointments
    # related to their patients
    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not doctor:

            return []

        query = query.filter(
            Appointment.doctor_id == doctor.id
        )

    return query.all()


# =========================
# GET APPOINTMENT BY ID
# =========================

@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get appointment by ID"
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:

        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    # Doctor restriction
    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not doctor or appointment.doctor_id != doctor.id:

            raise HTTPException(
                status_code=403,
                detail="You can only view your appointments"
            )

    return appointment


# =========================
# UPDATE APPOINTMENT
# =========================

@router.put(
    "/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Update appointment"
)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:

        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    # Doctor restriction
    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not doctor or appointment.doctor_id != doctor.id:

            raise HTTPException(
                status_code=403,
                detail="You can only update your appointments"
            )

    # Check doctor
    doctor = db.query(Doctor).filter(
        Doctor.id == appointment_data.doctor_id
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

    # Check patient
    patient = db.query(Patient).filter(
        Patient.id == appointment_data.patient_id
    ).first()

    if not patient:

        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    if patient.doctor_id != doctor.id:

        raise HTTPException(
            status_code=400,
            detail="Patient is not assigned to this doctor"
        )

    # Check overlap
    existing_appointment = db.query(Appointment).filter(
        Appointment.doctor_id == appointment_data.doctor_id,
        Appointment.appointment_date == appointment_data.appointment_date,
        Appointment.id != appointment_id,
        Appointment.status != "cancelled"
    ).first()

    if existing_appointment:

        raise HTTPException(
            status_code=400,
            detail="Doctor already has an appointment at this time"
        )

    appointment.doctor_id = appointment_data.doctor_id
    appointment.patient_id = appointment_data.patient_id
    appointment.appointment_date = appointment_data.appointment_date
    appointment.status = appointment_data.status

    db.commit()

    db.refresh(appointment)

    return appointment


# =========================
# DELETE APPOINTMENT
# =========================

@router.delete(
    "/{appointment_id}",
    summary="Delete appointment",
    description="Cancel an appointment. Admin only."
)
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(admin_required)
):

    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()

    if not appointment:

        raise HTTPException(
            status_code=404,
            detail="Appointment not found"
        )

    appointment.status = "cancelled"

    db.commit()

    return {
        "message": "Appointment cancelled successfully"
    }


# =========================
# DOCTOR APPOINTMENTS
# =========================

@router.get(
    "/doctor/{doctor_id}",
    response_model=list[AppointmentResponse],
    summary="Get doctor appointments"
)
def get_doctor_appointments(
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

    if current_user.role == "doctor":

        current_doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not current_doctor or current_doctor.id != doctor_id:

            raise HTTPException(
                status_code=403,
                detail="You can only view your own appointments"
            )

    return db.query(Appointment).filter(
        Appointment.doctor_id == doctor_id
    ).all()


# =========================
# PATIENT APPOINTMENTS
# =========================

@router.get(
    "/patient/{patient_id}",
    response_model=list[AppointmentResponse],
    summary="Get patient appointments"
)
def get_patient_appointments(
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

    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.email == current_user.email
        ).first()

        if not doctor or patient.doctor_id != doctor.id:

            raise HTTPException(
                status_code=403,
                detail="You can only view appointments for your patients"
            )

    return db.query(Appointment).filter(
        Appointment.patient_id == patient_id
    ).all()