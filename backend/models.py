from sqlalchemy import Date, ForeignKey, Integer, String
from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Application(Base):
    __tablename__ = "applications"

    user_id: Mapped[int | None] = mapped_column(
    Integer,
    ForeignKey("users.id"),
    nullable=True,
)

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    company: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    location: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        default="Not specified",
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Applied",
    )

    date_added: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )
from datetime import datetime, timezone
from sqlalchemy import DateTime

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )