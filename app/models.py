from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Numeric, CheckConstraint    
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="doctor")

    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)

    doctor = relationship(
    "Doctor",
    back_populates="user",
    foreign_keys=[doctor_id]
)

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    specialization = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=False)

    is_active = Column(Boolean, index=True, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    patients = relationship("Patient", back_populates="doctor")
    billings = relationship("Billing", back_populates="doctor")

    user = relationship(
        "User",
        back_populates="doctor",
        foreign_keys=[User.doctor_id]
    )


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    age = Column(Integer, index=True, nullable=False)
    phone = Column(String, nullable=False)

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False,
        index=True
    )


    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    doctor = relationship("Doctor", back_populates="patients")
    billings = relationship("Billing", back_populates="patient")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False,
        index=True
    )

    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False,
        index=True
    )

    appointment_date = Column(DateTime, nullable=False, index=True)

    status = Column(
        String,
        index=True,
        nullable=False,
    )

    billing = relationship("Billing", back_populates="appointment")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    doctor = relationship("Doctor")
    patient = relationship("Patient")


class Billing(Base):
    __tablename__ = "billings"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(
        Integer,
        ForeignKey("patients.id"),
        nullable=False,
        index=True
    )

    doctor_id = Column(
        Integer,
        ForeignKey("doctors.id"),
        nullable=False,
        index=True
    )

    appointment_id = Column(
        Integer,
        ForeignKey("appointments.id"),
        nullable=True,
        unique=True,
        index=True
    )

    consultation_fee = Column(
        Numeric(10, 2),
        nullable=False
    )

    additional_charges = Column(
        Numeric(10, 2),
        nullable=False,
        default=0
    )

    total_amount = Column(
        Numeric(10, 2),
        nullable=False
    )

    payment_status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )

    payment_mode = Column(
        String(20),
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "consultation_fee >= 0",
            name="check_consultation_fee_positive"
        ),

        CheckConstraint(
            "additional_charges >= 0",
            name="check_additional_charges_positive"
        ),

        CheckConstraint(
            "total_amount >= 0",
            name="check_total_amount_positive"
        ),

        CheckConstraint(
            "payment_status IN ('pending', 'paid', 'cancelled')",
            name="check_payment_status"
        ),

        CheckConstraint(
            "payment_mode IS NULL OR payment_mode IN ('cash', 'card', 'upi')",
            name="check_payment_mode"
        ),
    )

    patient = relationship(
        "Patient",
        back_populates="billings"
    )

    doctor = relationship(
        "Doctor",
        back_populates="billings"
    )

    appointment = relationship(
        "Appointment",
        back_populates="billing"
    )