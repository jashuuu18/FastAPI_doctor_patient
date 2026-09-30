import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from app.database import Base, engine
from app import models

from app.middleware import log_response_time

from app.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    database_exception_handler,
    general_exception_handler,
)

from app.routers import auth
from app.routers import doctors
from app.routers import patients
from app.routers import appointments
from app.routers import billings


# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


# =========================
# DATABASE
# =========================

Base.metadata.create_all(bind=engine)


# =========================
# FASTAPI APPLICATION
# =========================

app = FastAPI(
    title="Doctor Patient Management API",

    description="""
    REST API for managing doctors, patients, appointments,
    authentication, authorization, and role-based access.

    ### Features

    - User registration and login
    - JWT authentication
    - Admin and Doctor roles
    - Doctor management
    - Patient management
    - Doctor-patient assignment
    - Appointment management
    - Validation and error handling
    - SQLite database
    """,

    version="1.0.0"
)


# =========================
# EXCEPTION HANDLERS
# =========================

app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler
)

app.add_exception_handler(
    HTTPException,
    http_exception_handler
)

app.add_exception_handler(
    SQLAlchemyError,
    database_exception_handler
)

app.add_exception_handler(
    Exception,
    general_exception_handler
)


# =========================
# MIDDLEWARE
# =========================

app.middleware("http")(log_response_time)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173"
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# =========================
# ROUTERS
# =========================

app.include_router(auth.router)

app.include_router(doctors.router)

app.include_router(patients.router)

app.include_router(appointments.router)

app.include_router(billings.router)



# =========================
# HOME
# =========================

@app.get(
    "/",
    summary="API Home",
    description="Check whether the Doctor Patient Management API is running."
)
def home():

    return {
        "message": "Doctor Patient Management API is running"
    }