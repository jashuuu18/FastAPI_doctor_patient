from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import User

from app.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse
)

from app.auth.auth import (
    hash_password,
    verify_password,
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# =========================
# REGISTER
# =========================

@router.post("/register")
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    if user_data.role not in [
        "admin",
        "doctor"
    ]:

        raise HTTPException(
            status_code=400,
            detail="Role must be admin or doctor"
        )

    new_user = User(

        username=user_data.username,

        email=user_data.email,

        hashed_password=hash_password(
            user_data.password
        ),

        role=user_data.role
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return {
        "message": "User registered successfully"
    }




@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    try:
        print("LOGIN EMAIL:", login_data.email)

        user = db.query(User).filter(
            User.email == login_data.email
        ).first()

        print("USER FOUND:", user)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        print("HASHED PASSWORD:", user.hashed_password)

        password_valid = verify_password(
            login_data.password,
            user.hashed_password
        )

        print("PASSWORD VALID:", password_valid)

        if not password_valid:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        token = create_access_token({
            "user_id": user.id,
            "role": user.role
        })

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise

    except Exception as e:
        print("========== LOGIN ERROR ==========")
        print(type(e).__name__)
        print(str(e))
        print("=================================")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )