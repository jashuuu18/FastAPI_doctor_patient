# FastAPI_doctor_patient
## Level 27–29 – Billing & Payments Module

### Objective

Added a Billing and Payment management module to the Hospital Management FastAPI application.

### Billing Features

* Billing linked with Doctor, Patient, and Appointment.
* Consultation fee and additional charges.
* Total amount calculated automatically.
* Payment status:

  * `pending`
  * `paid`
  * `cancelled`
* Payment mode:

  * `cash`
  * `card`
  * `upi`
* Soft delete using `is_active`.
* Created and updated timestamps.

### Business Rules

* Patient must exist.
* Doctor must exist and be active.
* Appointment must belong to the selected Doctor and Patient.
* Cancelled appointments cannot be billed.
* Duplicate billing for the same appointment is prevented.
* `total_amount = consultation_fee + additional_charges`.
* Billing creation and appointment update use a database transaction.
* Database constraints protect invalid billing amounts and duplicate appointments.

### Billing APIs

```text
POST   /api/v1/billings
GET    /api/v1/billings
GET    /api/v1/billings/{billing_id}
PUT    /api/v1/billings/{billing_id}
PATCH  /api/v1/billings/{billing_id}
DELETE /api/v1/billings/{billing_id}

GET /api/v1/patients/{patient_id}/billings
GET /api/v1/doctors/{doctor_id}/billings

GET /api/v1/reports/revenue
```

### Filtering and Pagination

Billing list supports:

```text
payment_status
doctor_id
patient_id
from
to
page
limit
```

Example:

```text
GET /api/v1/billings?payment_status=paid&doctor_id=1&page=1&limit=10
```

### Revenue Reports

Revenue reports provide:

* Total revenue.
* Revenue per doctor.
* Revenue per day.
* Date-range filtering.
* Doctor filtering.

Only paid billing records are included in revenue calculations.

Example:

```text
GET /api/v1/reports/revenue?doctor_id=1&from=2026-09-01&to=2026-09-30
```

### Authorization

| Role              | Billing Access                      |
| ----------------- | ----------------------------------- |
| Admin             | Full billing access                 |
| Doctor            | View related billings               |
| Doctor            | Cannot create/update/delete billing |
| Unauthorized user | 403 Forbidden                       |

### Transaction Handling

Billing creation uses a database transaction:

```text
Create Billing
      ↓
Update Appointment
      ↓
Commit
```

If an error occurs:

```text
Error
 ↓
Rollback
```

This prevents partial database updates.

### Project Structure

```text
app/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── dependencies.py
├── middleware.py
├── exceptions.py
│
├── auth/
│   └── auth.py
│
└── routers/
    ├── auth.py
    ├── doctors.py
    ├── patients.py
    ├── appointments.py
    └── billings.py
```

### Testing

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Test:

1. Create Doctor.
2. Create Patient.
3. Create Appointment.
4. Login as Admin.
5. Authorize using JWT.
6. Create Billing.
7. Verify automatic total calculation.
8. Test duplicate billing.
9. Test cancelled appointment validation.
10. Test filtering and pagination.
11. Test patient and doctor billing APIs.
12. Test revenue reports.
13. Test Doctor authorization.
14. Test soft delete.

### Submission

* Updated GitHub repository.
* Swagger/Postman screenshots.
* Updated README.
* Billing APIs tested successfully.
* Revenue reports tested successfully.
* Authorization and transaction handling verified.
