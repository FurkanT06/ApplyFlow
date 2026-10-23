import jwt
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from auth import JWT_SECRET_KEY, JWT_ALGORITHM

import os
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import hash_password, verify_password, create_access_token
from database import Base, engine, get_db
from models import Application as ApplicationModel, User


# --------------------
# Pydantic models
# --------------------

ApplicationStatus = Literal[
    "Applied", "Interview", "Offer", "Rejected"
]


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=160)
    location: str = Field(
        default="Not specified", min_length=1, max_length=120
    )
    status: ApplicationStatus = "Applied"


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, min_length=1, max_length=160)
    location: str | None = Field(default=None, min_length=1, max_length=120)
    status: ApplicationStatus | None = None


class Application(ApplicationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_added: date


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --------------------
# FastAPI setup
# --------------------

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ApplyFlow API",
    description="API for tracking job applications.",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        if not JWT_SECRET_KEY:
            raise RuntimeError("JWT_SECRET_KEY is not configured")

        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = int(payload["sub"])

    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# --------------------
# Health endpoints
# --------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to ApplyFlow API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --------------------
# Application endpoints
# --------------------


@app.get("/api/applications", response_model=list[Application])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(ApplicationModel)
        .where(ApplicationModel.user_id == current_user.id)
        .order_by(
            ApplicationModel.date_added.desc(),
            ApplicationModel.id.desc(),
        )
    ).all()

@app.post(
    "/api/applications",
    response_model=Application,
    status_code=201,
)

@app.post(
    "/api/applications",
    response_model=Application,
    status_code=201,
)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = ApplicationModel(
        **payload.model_dump(),
        user_id=current_user.id,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application

@app.patch(
    "/api/applications/{application_id}",
    response_model=Application,
)

@app.patch(
    "/api/applications/{application_id}",
    response_model=Application,
)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.scalar(
        select(ApplicationModel).where(
            ApplicationModel.id == application_id,
            ApplicationModel.user_id == current_user.id,
        )
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    for field, value in payload.model_dump(
        exclude_none=True
    ).items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)

    return application

    application = db.get(ApplicationModel, application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    for field, value in payload.model_dump(
        exclude_none=True
    ).items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)

    return application


@app.delete(
    "/api/applications/{application_id}",
    status_code=204,
)

@app.delete(
    "/api/applications/{application_id}",
    status_code=204,
)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    application = db.scalar(
        select(ApplicationModel).where(
            ApplicationModel.id == application_id,
            ApplicationModel.user_id == current_user.id,
        )
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    db.delete(application)
    db.commit()

    return Response(status_code=204)

    application = db.get(ApplicationModel, application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    db.delete(application)
    db.commit()

    return Response(status_code=204)


# --------------------
# Authentication endpoints
# --------------------

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=201,
)
def register_user(
    payload: UserRegister,
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower()

    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    db.refresh(user)
    return user


@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login_user(
    payload: UserLogin,
    db: Session = Depends(get_db),
):
    email = str(payload.email).lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None or not verify_password(
        payload.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)

    return TokenResponse(access_token=token)
