
from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Application(Base):
    __tablename__ = "applications"

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
