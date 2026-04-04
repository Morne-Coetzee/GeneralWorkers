from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(String(20), nullable=False)  # "employer" or "worker"
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job_postings = relationship("JobPosting", back_populates="employer", foreign_keys="JobPosting.employer_id")
    worker_profile = relationship("WorkerProfile", back_populates="worker", uselist=False, foreign_keys="WorkerProfile.worker_id")
    job_applications = relationship("JobApplication", back_populates="worker", foreign_keys="JobApplication.worker_id")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, index=True)
    employer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location = Column(String(255), nullable=False)
    pay_rate = Column(String(100), nullable=False)
    job_type = Column(String(50), nullable=False)  # "once-off", "part-time", "full-time"
    skills_required = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    employer = relationship("User", back_populates="job_postings", foreign_keys=[employer_id])
    applications = relationship("JobApplication", back_populates="job", foreign_keys="JobApplication.job_id")


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    bio = Column(Text, nullable=True)
    skills = Column(Text, nullable=False)  # comma-separated
    experience = Column(Text, nullable=True)
    availability = Column(String(50), nullable=False)  # "immediately", "within-week", "within-month"
    preferred_job_type = Column(String(50), nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    worker = relationship("User", back_populates="worker_profile", foreign_keys=[worker_id])


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # "pending", "accepted", "rejected"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("JobPosting", back_populates="applications", foreign_keys=[job_id])
    worker = relationship("User", back_populates="job_applications", foreign_keys=[worker_id])
