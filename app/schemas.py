from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── User schemas ──────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    user_type: str  # "employer" or "worker"
    phone: Optional[str] = None
    location: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    user_type: str
    full_name: str
    phone: Optional[str]
    location: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── JobPosting schemas ────────────────────────────────────────────────────────

class JobPostingCreate(BaseModel):
    title: str
    description: str
    location: str
    pay_rate: str
    job_type: str
    skills_required: Optional[str] = None


class JobPostingOut(BaseModel):
    id: int
    employer_id: int
    title: str
    description: str
    location: str
    pay_rate: str
    job_type: str
    skills_required: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── WorkerProfile schemas ─────────────────────────────────────────────────────

class WorkerProfileCreate(BaseModel):
    bio: Optional[str] = None
    skills: str
    experience: Optional[str] = None
    availability: str
    preferred_job_type: str
    is_available: bool = True


class WorkerProfileOut(BaseModel):
    id: int
    worker_id: int
    bio: Optional[str]
    skills: str
    experience: Optional[str]
    availability: str
    preferred_job_type: str
    is_available: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── JobApplication schemas ────────────────────────────────────────────────────

class JobApplicationCreate(BaseModel):
    job_id: int
    message: Optional[str] = None


class JobApplicationOut(BaseModel):
    id: int
    job_id: int
    worker_id: int
    message: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
