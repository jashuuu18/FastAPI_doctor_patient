from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field


# ============================================================
# Authentication Schemas
# ============================================================

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "doctor"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ============================================================
# Doctor Schemas
# ============================================================

class DoctorCreate(BaseModel):
    name: str
    email: EmailStr
    specialization: str
    phone: str = Field(pattern=r"^\d{10}$")


class DoctorUpdate(BaseModel):
    name: str
    email: EmailStr
    specialization: str
    phone: str = Field(pattern=r"^\d{10}$")


class DoctorPatch(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    specialization: Optional[str] = None
    phone: Optional[str] = Field(
        default=None,
        pattern=r"^\d{10}$"
    )
    is_active: Optional[bool] = None


class DoctorResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    specialization: str
    phone: str
    is_active: bool

    model_config = {
        "from_attributes": True
    }


# ============================================================
# Patient Schemas
# ============================================================

class PatientCreate(BaseModel):
    name: str
    age: int = Field(gt=0)
    phone: str = Field(pattern=r"^\d{10}$")
    doctor_id: int


class PatientUpdate(BaseModel):
    name: str
    age: int = Field(gt=0)
    phone: str = Field(pattern=r"^\d{10}$")
    doctor_id: int


class PatientPatch(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(
        default=None,
        gt=0
    )
    phone: Optional[str] = Field(
        default=None,
        pattern=r"^\d{10}$"
    )
    doctor_id: Optional[int] = None


class PatientResponse(BaseModel):
    id: int
    name: str
    age: int
    phone: str
    doctor_id: int

    model_config = {
        "from_attributes": True
    }


# ============================================================
# Appointment Schemas
# ============================================================

class AppointmentStatus(str, Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_date: datetime
    status: AppointmentStatus = AppointmentStatus.scheduled


class AppointmentUpdate(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_date: datetime
    status: AppointmentStatus


class AppointmentResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    appointment_date: datetime
    status: AppointmentStatus

    model_config = {
        "from_attributes": True
    }


# ============================================================
# Billing Schemas
# ============================================================

class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    cancelled = "cancelled"


class PaymentMode(str, Enum):
    cash = "cash"
    card = "card"
    upi = "upi"


# ------------------------------------------------------------
# Create Billing
# ------------------------------------------------------------

class BillingCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_id: Optional[int] = None

    consultation_fee: Decimal = Field(
        ...,
        ge=0
    )

    additional_charges: Decimal = Field(
        default=Decimal("0.00"),
        ge=0
    )

    payment_status: PaymentStatus = PaymentStatus.pending

    payment_mode: Optional[PaymentMode] = None


# ------------------------------------------------------------
# Full Update Billing
# ------------------------------------------------------------

class BillingUpdate(BaseModel):
    consultation_fee: Decimal = Field(
        ...,
        ge=0
    )

    additional_charges: Decimal = Field(
        ...,
        ge=0
    )

    payment_status: PaymentStatus

    payment_mode: Optional[PaymentMode] = None


# ------------------------------------------------------------
# Partial Update Billing
# ------------------------------------------------------------

class BillingPatch(BaseModel):
    consultation_fee: Optional[Decimal] = Field(
        default=None,
        ge=0
    )

    additional_charges: Optional[Decimal] = Field(
        default=None,
        ge=0
    )

    payment_status: Optional[PaymentStatus] = None

    payment_mode: Optional[PaymentMode] = None


# ------------------------------------------------------------
# Billing Response
# ------------------------------------------------------------

class BillingResponse(BaseModel):
    id: int

    patient_id: int
    doctor_id: int
    appointment_id: Optional[int]

    consultation_fee: Decimal
    additional_charges: Decimal
    total_amount: Decimal

    payment_status: PaymentStatus
    payment_mode: Optional[PaymentMode]

    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


# ------------------------------------------------------------
# Billing List / Pagination Response
# ------------------------------------------------------------

class BillingListResponse(BaseModel):
    total: int
    page: int
    limit: int
    data: List[BillingResponse]