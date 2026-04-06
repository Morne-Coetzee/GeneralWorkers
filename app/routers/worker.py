import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import User, JobPosting, WorkerProfile, JobApplication, Skill

router = APIRouter(prefix="/worker", tags=["worker"])

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


def get_worker(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type")
    if not user_id or user_type != "worker":
        return None
    return db.query(User).filter(User.id == user_id).first()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_worker(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    profile = db.query(WorkerProfile).filter(WorkerProfile.worker_id == user.id).first()

    # Worker's applications
    applications = (
        db.query(JobApplication)
        .filter(JobApplication.worker_id == user.id)
        .order_by(JobApplication.created_at.desc())
        .all()
    )

    # Recent active jobs to show as opportunities
    recent_jobs = (
        db.query(JobPosting)
        .filter(JobPosting.is_active == True)
        .order_by(JobPosting.created_at.desc())
        .limit(5)
        .all()
    )

    applied_job_ids = {app.job_id for app in applications}

    flash_success = request.session.pop("flash_success", None)
    flash_error = request.session.pop("flash_error", None)

    return templates.TemplateResponse(request, "worker/dashboard.html", {
        "user": user,
        "profile": profile,
        "applications": applications,
        "recent_jobs": recent_jobs,
        "applied_job_ids": applied_job_ids,
        "flash_success": flash_success,
        "flash_error": flash_error,
    })


# ── Worker Profile ────────────────────────────────────────────────────────────

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_worker(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    profile = db.query(WorkerProfile).filter(WorkerProfile.worker_id == user.id).first()
    all_skills = db.query(Skill).order_by(Skill.name).all()
    selected_ids = {s.id for s in profile.skills} if profile else set()
    flash_success = request.session.pop("flash_success", None)
    flash_error = request.session.pop("flash_error", None)

    return templates.TemplateResponse(request, "worker/create_profile.html", {
        "user": user,
        "profile": profile,
        "all_skills": all_skills,
        "selected_ids": selected_ids,
        "flash_success": flash_success,
        "flash_error": flash_error,
    })


@router.post("/profile")
async def save_profile(
    request: Request,
    bio: str = Form(""),
    experience: str = Form(""),
    availability: str = Form(...),
    preferred_job_type: str = Form(...),
    is_available: str = Form("off"),
    db: Session = Depends(get_db)
):
    user = get_worker(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    form = await request.form()
    skill_ids = [int(v) for v in form.getlist("skill_ids") if v.isdigit()]

    if not skill_ids:
        request.session["flash_error"] = "Please select at least one skill."
        return RedirectResponse(url="/worker/profile", status_code=302)

    if availability not in ("immediately", "within-week", "within-month"):
        request.session["flash_error"] = "Invalid availability option."
        return RedirectResponse(url="/worker/profile", status_code=302)

    if preferred_job_type not in ("once-off", "part-time", "full-time", "any"):
        request.session["flash_error"] = "Invalid job type preference."
        return RedirectResponse(url="/worker/profile", status_code=302)

    selected_skills = db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
    available = is_available == "on"

    profile = db.query(WorkerProfile).filter(WorkerProfile.worker_id == user.id).first()
    if profile:
        profile.bio = bio.strip() or None
        profile.experience = experience.strip() or None
        profile.availability = availability
        profile.preferred_job_type = preferred_job_type
        profile.is_available = available
        profile.skills = selected_skills
    else:
        profile = WorkerProfile(
            worker_id=user.id,
            bio=bio.strip() or None,
            experience=experience.strip() or None,
            availability=availability,
            preferred_job_type=preferred_job_type,
            is_available=available,
            skills=selected_skills,
        )
        db.add(profile)

    db.commit()
    request.session["flash_success"] = "Profile saved successfully!"
    return RedirectResponse(url="/worker/dashboard", status_code=302)


# ── Browse Jobs ───────────────────────────────────────────────────────────────

@router.get("/browse-jobs", response_class=HTMLResponse)
async def browse_jobs(
    request: Request,
    search: str = "",
    job_type: str = "",
    location: str = "",
    db: Session = Depends(get_db)
):
    user = get_worker(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    query = db.query(JobPosting).filter(JobPosting.is_active == True)

    if job_type:
        query = query.filter(JobPosting.job_type == job_type)
    if location:
        query = query.filter(JobPosting.location.ilike(f"%{location}%"))
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            JobPosting.title.ilike(search_term) |
            JobPosting.description.ilike(search_term) |
            JobPosting.skills_required.ilike(search_term)
        )

    jobs = query.order_by(JobPosting.created_at.desc()).all()

    # Track which jobs the worker has already applied to
    applications = db.query(JobApplication).filter(JobApplication.worker_id == user.id).all()
    applied_job_ids = {app.job_id for app in applications}

    flash_success = request.session.pop("flash_success", None)
    flash_error = request.session.pop("flash_error", None)

    return templates.TemplateResponse(request, "worker/browse_jobs.html", {
        "user": user,
        "jobs": jobs,
        "applied_job_ids": applied_job_ids,
        "search": search,
        "job_type": job_type,
        "location": location,
        "flash_success": flash_success,
        "flash_error": flash_error,
    })


# ── Apply to Job ──────────────────────────────────────────────────────────────

@router.post("/apply/{job_id}")
async def apply_to_job(
    request: Request,
    job_id: int,
    message: str = Form(""),
    db: Session = Depends(get_db)
):
    user = get_worker(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    # Check if already applied
    existing = db.query(JobApplication).filter(
        JobApplication.job_id == job_id,
        JobApplication.worker_id == user.id
    ).first()

    if existing:
        request.session["flash_error"] = "You have already applied to this job."
        return RedirectResponse(url="/worker/browse-jobs", status_code=302)

    # Verify job exists and is active
    job = db.query(JobPosting).filter(JobPosting.id == job_id, JobPosting.is_active == True).first()
    if not job:
        request.session["flash_error"] = "Job not found or no longer active."
        return RedirectResponse(url="/worker/browse-jobs", status_code=302)

    application = JobApplication(
        job_id=job_id,
        worker_id=user.id,
        message=message.strip() or None,
        status="pending",
    )
    db.add(application)
    db.commit()

    request.session["flash_success"] = f"Application submitted for '{job.title}'!"
    return RedirectResponse(url="/worker/browse-jobs", status_code=302)


# ── Withdraw Application ──────────────────────────────────────────────────────

@router.post("/application/{app_id}/withdraw")
async def withdraw_application(
    request: Request,
    app_id: int,
    db: Session = Depends(get_db)
):
    user = get_worker(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    application = db.query(JobApplication).filter(
        JobApplication.id == app_id,
        JobApplication.worker_id == user.id,
        JobApplication.status == "pending"
    ).first()

    if application:
        db.delete(application)
        db.commit()
        request.session["flash_success"] = "Application withdrawn."
    else:
        request.session["flash_error"] = "Application not found or cannot be withdrawn."

    return RedirectResponse(url="/worker/dashboard", status_code=302)
