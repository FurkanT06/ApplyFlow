
from sqlalchemy import Column, Integer, String, DateTime, func
from database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(150), nullable=False)
    role = Column(String(150), nullable=False)
    status = Column(String(50), nullable=False, default="Applied")
    location = Column(String(150), nullable=True)
    job_url = Column(String(500), nullable=True)
    notes = Column(String(2000), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
