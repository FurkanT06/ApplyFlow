import os
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

DB_PATH = os.getenv("APPLYFLOW_DB", "applyflow.db")
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

ApplicationStatus = Literal["Applied", "Interview", "Offer", "Rejected"]


# ---------- Schemas ----------


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=160)
    location: str = Field(default="Not specified", min_length=1, max_length=120)
    status: ApplicationStatus = "Applied"


class ApplicationUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    company: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, min_length=1, max_length=160)
    location: str | None = Field(default=None, min_length=1, max_length=120)
    status: ApplicationStatus | None = None


class Application(ApplicationCreate):
    id: int
    date_added: date


# ---------- Database ----------


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT 'Not specified',
                status TEXT NOT NULL DEFAULT 'Applied',
                date_added TEXT NOT NULL
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        if count == 0:
            today = date.today().isoformat()
            conn.executemany(
                "INSERT INTO applications (company, role, location, status, date_added)"
                " VALUES (?, ?, ?, ?, ?)",
                [
                    ("Google", "Software Engineer, New Grad", "Mountain View, CA", "Interview", today),
                    ("Stripe", "Software Engineer", "Remote", "Applied", today),
                ],
            )


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


# ---------- App ----------

app = FastAPI(
    title="ApplyFlow API",
    description="API for tracking job applications.",
    version="0.2.0",
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
def list_applications():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM applications ORDER BY date_added DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/applications", response_model=Application, status_code=201)
def create_application(payload: ApplicationCreate):
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO applications (company, role, location, status, date_added)"
            " VALUES (?, ?, ?, ?, ?)",
            (
                payload.company,
                payload.role,
                payload.location,
                payload.status,
                date.today().isoformat(),
            ),
        )
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return dict(row)


@app.patch("/api/applications/{application_id}", response_model=Application)
def update_application(application_id: int, payload: ApplicationUpdate):
    changes = payload.model_dump(exclude_none=True)
    with get_db() as conn:
        if changes:
            assignments = ", ".join(f"{column} = ?" for column in changes)
            cursor = conn.execute(
                f"UPDATE applications SET {assignments} WHERE id = ?",
                (*changes.values(), application_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Application not found")
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (application_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Application not found")
    return dict(row)


@app.delete("/api/applications/{application_id}", status_code=204)
def delete_application(application_id: int):
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM applications WHERE id = ?", (application_id,)
        )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    return Response(status_code=204)

