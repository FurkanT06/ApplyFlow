
import os
from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Application as ApplicationModel

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

ApplicationStatus = Literal["Applied", "Interview", "Offer", "Rejected"]


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


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ApplyFlow API",
    description="API for tracking job applications.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Welcome to ApplyFlow API", "status": "running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/applications", response_model=list[Application])
def list_applications(db: Session = Depends(get_db)):
    return db.scalars(
        select(ApplicationModel).order_by(
            ApplicationModel.date_added.desc(),
            ApplicationModel.id.desc(),
        )
    ).all()


@app.post("/api/applications", response_model=Application, status_code=201)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
):
    application = ApplicationModel(**payload.model_dump())
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@app.patch("/api/applications/{application_id}", response_model=Application)
def update_application(
    application_id: int,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
):
    application = db.get(ApplicationModel, application_id)

    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)
    return application


@app.delete("/api/applications/{application_id}", status_code=204)
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = db.get(ApplicationModel, application_id)

    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(application)
    db.commit()
    return Response(status_code=204)
