from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Billing, Doctor, Patient, Appointment
from app.schemas import (
    BillingCreate,
    BillingResponse,
    BillingListResponse,
    BillingUpdate,
    BillingPatch
)
from app.dependencies import get_current_user


# ============================================================
# BILLING ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/v1/billings",
    tags=["Billings"]
)


# ============================================================
# 1. HELPER - GET BILLING
# ============================================================

def get_billing_or_404(
    billing_id: int,
    db: Session
):
    billing = (
        db.query(Billing)
        .filter(
            Billing.id == billing_id,
            Billing.is_active == True
        )
        .first()
    )

    if not billing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billing not found"
        )

    return billing


# ============================================================
# 2. DOCTOR AUTHORIZATION
# ============================================================

def authorize_doctor_for_billing(
    billing: Billing,
    current_user,
    db: Session
):
    if current_user.role == "admin":
        return

    doctor = (
        db.query(Doctor)
        .filter(
            Doctor.email == current_user.email
        )
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor profile not found"
        )

    if billing.doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this billing"
        )


# ============================================================
# 3. CREATE BILLING
# ============================================================

@router.post(
    "",
    response_model=BillingResponse,
    status_code=status.HTTP_201_CREATED
)
def create_billing(
    billing_data: BillingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # Only admin and doctor
    if current_user.role not in ["admin", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to create billing"
        )

    # Check patient
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == billing_data.patient_id
        )
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Check doctor
    doctor = (
        db.query(Doctor)
        .filter(
            Doctor.id == billing_data.doctor_id
        )
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    # Doctor must be active
    if not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create billing for inactive doctor"
        )

    # Doctor can only create billing for themselves
    if current_user.role == "doctor":

        logged_doctor = (
            db.query(Doctor)
            .filter(
                Doctor.email == current_user.email
            )
            .first()
        )

        if not logged_doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found"
            )

        if logged_doctor.id != billing_data.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can create billing only for yourself"
            )

        if patient.doctor_id != logged_doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This patient is not assigned to you"
            )

    # Appointment validation
    if billing_data.appointment_id is not None:

        appointment = (
            db.query(Appointment)
            .filter(
                Appointment.id == billing_data.appointment_id
            )
            .first()
        )

        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )

        if appointment.doctor_id != billing_data.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment does not belong to this doctor"
            )

        if appointment.patient_id != billing_data.patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Appointment does not belong to this patient"
            )

        if appointment.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create billing for cancelled appointment"
            )

        existing_billing = (
            db.query(Billing)
            .filter(
                Billing.appointment_id ==
                billing_data.appointment_id
            )
            .first()
        )

        if existing_billing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Billing already exists for this appointment"
            )

    # Calculate total
    total_amount = (
        billing_data.consultation_fee
        + billing_data.additional_charges
    )

    # Create billing
    new_billing = Billing(
        patient_id=billing_data.patient_id,
        doctor_id=billing_data.doctor_id,
        appointment_id=billing_data.appointment_id,
        consultation_fee=billing_data.consultation_fee,
        additional_charges=billing_data.additional_charges,
        total_amount=total_amount,
        payment_status=billing_data.payment_status.value,
        payment_mode=(
            billing_data.payment_mode.value
            if billing_data.payment_mode
            else None
        ),
        is_active=True
    )

    db.add(new_billing)

    db.commit()

    db.refresh(new_billing)

    return new_billing


# ============================================================
# 4. GET PATIENT BILLINGS
# ============================================================

@router.get(
    "/patients/{patient_id}/billings",
    response_model=BillingListResponse
)
def get_patient_billings(
    patient_id: int,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )

    # Check patient
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == patient_id
        )
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Doctor authorization
    if current_user.role == "doctor":

        doctor = (
            db.query(Doctor)
            .filter(
                Doctor.email == current_user.email
            )
            .first()
        )

        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found"
            )

        if patient.doctor_id != doctor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this patient's billing"
            )

    elif current_user.role != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view billing"
        )

    # Get billing
    query = (
        db.query(Billing)
        .filter(
            Billing.patient_id == patient_id,
            Billing.is_active == True
        )
    )

    total = query.count()

    billings = (
        query
        .order_by(Billing.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": billings
    }


# ============================================================
# 5. GET DOCTOR BILLINGS
# ============================================================

@router.get(
    "/doctors/{doctor_id}/billings",
    response_model=BillingListResponse
)
def get_doctor_billings(
    doctor_id: int,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )

    doctor = (
        db.query(Doctor)
        .filter(
            Doctor.id == doctor_id
        )
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    # Doctor can see only their own billing
    if current_user.role == "doctor":

        logged_doctor = (
            db.query(Doctor)
            .filter(
                Doctor.email == current_user.email
            )
            .first()
        )

        if not logged_doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found"
            )

        if logged_doctor.id != doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this doctor's billing"
            )

    elif current_user.role != "admin":

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view billing"
        )

    query = (
        db.query(Billing)
        .filter(
            Billing.doctor_id == doctor_id,
            Billing.is_active == True
        )
    )

    total = query.count()

    billings = (
        query
        .order_by(Billing.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": billings
    }

# ============================================================
#  GET ALL BILLINGS WITH FILTERS
# ============================================================

@router.get(
    "",
    response_model=BillingListResponse
)
def get_billings(
    payment_status: str | None = None,
    doctor_id: int | None = None,
    patient_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    # --------------------------------------------------------
    # Authorization
    # --------------------------------------------------------

    if current_user.role not in ["admin", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view billing"
        )

    # --------------------------------------------------------
    # Pagination validation
    # --------------------------------------------------------

    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )

    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )

    # --------------------------------------------------------
    # Base query
    # --------------------------------------------------------

    query = (
        db.query(Billing)
        .filter(
            Billing.is_active == True
        )
    )

    # --------------------------------------------------------
    # Doctor restriction
    # --------------------------------------------------------

    if current_user.role == "doctor":

        logged_doctor = (
            db.query(Doctor)
            .filter(
                Doctor.email == current_user.email
            )
            .first()
        )

        if not logged_doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found"
            )

        query = query.filter(
            Billing.doctor_id == logged_doctor.id
        )

    # --------------------------------------------------------
    # Payment status filter
    # --------------------------------------------------------

    if payment_status is not None:

        allowed_statuses = [
            "pending",
            "paid",
            "cancelled"
        ]

        if payment_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payment status"
            )

        query = query.filter(
            Billing.payment_status == payment_status
        )

    # --------------------------------------------------------
    # Doctor ID filter
    # --------------------------------------------------------

    if doctor_id is not None:

        query = query.filter(
            Billing.doctor_id == doctor_id
        )

    # --------------------------------------------------------
    # Patient ID filter
    # --------------------------------------------------------

    if patient_id is not None:

        query = query.filter(
            Billing.patient_id == patient_id
        )

    # --------------------------------------------------------
    # From date filter
    # --------------------------------------------------------

    if from_date is not None:

        query = query.filter(
            Billing.created_at >= from_date
        )

    # --------------------------------------------------------
    # To date filter
    # --------------------------------------------------------

    if to_date is not None:

        query = query.filter(
            Billing.created_at <= to_date
        )

    # --------------------------------------------------------
    # Total records
    # --------------------------------------------------------

    total = query.count()

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    billings = (
        query
        .order_by(
            Billing.created_at.desc()
        )
        .offset(
            (page - 1) * limit
        )
        .limit(limit)
        .all()
    )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": billings
    }

# =========================================================
#  - REVENUE PER DOCTOR
# =========================================================

@router.get("/reports/revenue/doctors")
def revenue_per_doctor(
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can view doctor revenue"
        )

    query = (
        db.query(
            Billing.doctor_id,
            func.sum(Billing.total_amount).label("total_revenue")
        )
        .filter(
            Billing.is_active == True,
            Billing.payment_status == "paid"
        )
    )

    if from_date is not None:
        query = query.filter(Billing.created_at >= from_date)

    if to_date is not None:
        query = query.filter(Billing.created_at <= to_date)

    results = (
        query
        .group_by(Billing.doctor_id)
        .order_by(Billing.doctor_id)
        .all()
    )

    return [
        {
            "doctor_id": doctor_id,
            "total_revenue": total_revenue
        }
        for doctor_id, total_revenue in results
    ]


# =========================================================
#  - REVENUE PER DAY
# =========================================================

@router.get("/reports/revenue/daily")
def revenue_per_day(
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can view daily revenue"
        )

    query = (
        db.query(
            func.date(Billing.created_at).label("revenue_date"),
            func.sum(Billing.total_amount).label("total_revenue")
        )
        .filter(
            Billing.is_active == True,
            Billing.payment_status == "paid"
        )
    )

    if from_date is not None:
        query = query.filter(Billing.created_at >= from_date)

    if to_date is not None:
        query = query.filter(Billing.created_at <= to_date)

    results = (
        query
        .group_by(func.date(Billing.created_at))
        .order_by(func.date(Billing.created_at))
        .all()
    )

    return [
        {
            "date": revenue_date,
            "total_revenue": total_revenue
        }
        for revenue_date, total_revenue in results
    ]


# =========================================================
# - TOTAL REVENUE REPORT
# =========================================================

@router.get("/reports/revenue")
def revenue_report(
    doctor_id: int | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can view revenue report"
        )

    if from_date is not None and to_date is not None:
        if from_date > to_date:
            raise HTTPException(
                status_code=400,
                detail="from_date cannot be greater than to_date"
            )

    query = (
        db.query(
            func.sum(Billing.total_amount).label("total_revenue")
        )
        .filter(
            Billing.is_active == True,
            Billing.payment_status == "paid"
        )
    )

    if doctor_id is not None:
        doctor = db.query(Doctor).filter(
            Doctor.id == doctor_id
        ).first()

        if not doctor:
            raise HTTPException(
                status_code=404,
                detail="Doctor not found"
            )

        query = query.filter(Billing.doctor_id == doctor_id)

    if from_date is not None:
        query = query.filter(Billing.created_at >= from_date)

    if to_date is not None:
        query = query.filter(Billing.created_at <= to_date)

    total_revenue = query.scalar() or 0

    return {
        "doctor_id": doctor_id,
        "from_date": from_date,
        "to_date": to_date,
        "total_revenue": total_revenue
    }


# ============================================================
# 6. GET BILLING BY ID
# ============================================================

@router.get(
    "/{billing_id}",
    response_model=BillingResponse
)
def get_billing(
    billing_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    billing = get_billing_or_404(
        billing_id,
        db
    )

    authorize_doctor_for_billing(
        billing,
        current_user,
        db
    )

    return billing




# ============================================================
# 7. UPDATE BILLING - PUT
# ============================================================

@router.put(
    "/{billing_id}",
    response_model=BillingResponse
)
def update_billing(
    billing_id: int,
    billing_data: BillingUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    billing = get_billing_or_404(
        billing_id,
        db
    )

    if current_user.role == "admin":
        pass

    elif current_user.role == "doctor":

        authorize_doctor_for_billing(
            billing,
            current_user,
            db
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update billing"
        )

    billing.consultation_fee = (
        billing_data.consultation_fee
    )

    billing.additional_charges = (
        billing_data.additional_charges
    )

    billing.payment_status = (
        billing_data.payment_status.value
    )

    billing.payment_mode = (
        billing_data.payment_mode.value
        if billing_data.payment_mode
        else None
    )

    billing.total_amount = (
        billing.consultation_fee
        + billing.additional_charges
    )

    db.commit()

    db.refresh(billing)

    return billing


# ============================================================
# 8. UPDATE BILLING - PATCH
# ============================================================

@router.patch(
    "/{billing_id}",
    response_model=BillingResponse
)
def patch_billing(
    billing_id: int,
    billing_data: BillingPatch,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    billing = get_billing_or_404(
        billing_id,
        db
    )

    if current_user.role == "admin":
        pass

    elif current_user.role == "doctor":

        authorize_doctor_for_billing(
            billing,
            current_user,
            db
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update billing"
        )

    update_data = billing_data.model_dump(
        exclude_unset=True
    )

    if "consultation_fee" in update_data:

        billing.consultation_fee = (
            update_data["consultation_fee"]
        )

    if "additional_charges" in update_data:

        billing.additional_charges = (
            update_data["additional_charges"]
        )

    if "payment_status" in update_data:

        billing.payment_status = (
            update_data["payment_status"].value
        )

    if "payment_mode" in update_data:

        billing.payment_mode = (
            update_data["payment_mode"].value
            if update_data["payment_mode"]
            else None
        )

    billing.total_amount = (
        billing.consultation_fee
        + billing.additional_charges
    )

    db.commit()

    db.refresh(billing)

    return billing


# ============================================================
# 9. DELETE BILLING - SOFT DELETE
# ============================================================

@router.delete(
    "/{billing_id}",
    status_code=status.HTTP_200_OK
)
def delete_billing(
    billing_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    billing = get_billing_or_404(
        billing_id,
        db
    )

    # Only admin can delete
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete billing"
        )

    billing.is_active = False

    db.commit()

    return {
        "message": "Billing deleted successfully",
        "billing_id": billing.id
    }

