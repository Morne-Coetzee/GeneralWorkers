import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import User, JobPosting, WorkerProfile, JobApplication

router = APIRouter(prefix="/employer", tags=["employer"])

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


def get_employer(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type")
    if not user_id or user_type != "employer":
        return None
    return db.query(User).filter(User.id == user_id).first()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_employer(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    job_postings = db.query(JobPosting).filter(
        JobPosting.employer_id == user.id
    ).order_by(JobPosting.created_at.desc()).all()

    # Gather recent applicants across all job postings
    job_ids = [j.id for j in job_postings]
    recent_applications = []
    if job_ids:
        recent_applications = (
            db.query(JobApplication)
            .filter(JobApplication.job_id.in_(job_ids))
            .order_by(JobApplication.created_at.desc())
            .limit(10)
            .all()
        )

    # Count stats
    active_jobs = sum(1 for j in job_postings if j.is_active)
    total_applications = sum(len(j.applications) for j in job_postings)
    pending_applications = sum(
        1 for app in recent_applications if app.status == "pending"
    )

    flash_success = request.session.pop("flash_success", None)
    flash_error = request.session.pop("flash_error", None)

    return templates.TemplateResponse(request, "employer/dashboard.html", {
        "user": user,
        "job_postings": job_postings,
        "recent_applications": recent_applications,
        "active_jobs": active_jobs,
        "total_applications": total_applications,
        "pending_applications": pending_applications,
        "flash_success": flash_success,
        "flash_error": flash_error,
    })


# ── Post Job ──────────────────────────────────────────────────────────────────

@router.get("/post-job", response_class=HTMLResponse)
async def post_job_page(request: Request, db: Session = Depends(get_db)):
    user = get_employer(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    flash_error = request.session.pop("flash_error", None)
    return templates.TemplateResponse(request, "employer/post_job.html", {
        "user": user,
        "flash_error": flash_error,
    })


@router.post("/post-job")
async def post_job(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    pay_rate: str = Form(...),
    job_type: str = Form(...),
    skills_required: str = Form(""),
    db: Session = Depends(get_db)
):
    user = get_employer(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if job_type not in ("once-off", "part-time", "full-time"):
        request.session["flash_error"] = "Invalid job type."
        return RedirectResponse(url="/employer/post-job", status_code=302)

    job = JobPosting(
        employer_id=user.id,
        title=title.strip(),
        description=description.strip(),
        location=location.strip(),
        pay_rate=pay_rate.strip(),
        job_type=job_type,
        skills_required=skills_required.strip() or None,
        is_active=True,
    )
    db.add(job)
    db.commit()
    request.session["flash_success"] = "Job posted successfully!"
    return RedirectResponse(url="/employer/dashboard", status_code=302)


# ── Toggle Job Active/Inactive ────────────────────────────────────────────────

@router.post("/job/{job_id}/toggle")
async def toggle_job(
    request: Request,
    job_id: int,
    db: Session = Depends(get_db)
):
    user = get_employer(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.employer_id == user.id
    ).first()

    if job:
        job.is_active = not job.is_active
        db.commit()
        status_text = "activated" if job.is_active else "deactivated"
        request.session["flash_success"] = f"Job listing {status_text}."
    else:
        request.session["flash_error"] = "Job not found."

    return RedirectResponse(url="/employer/dashboard", status_code=302)


# ── Delete Job ────────────────────────────────────────────────────────────────

@router.post("/job/{job_id}/delete")
async def delete_job(
    request: Request,
    job_id: int,
    db: Session = Depends(get_db)
):
    user = get_employer(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    job = db.query(JobPosting).filter(
        JobPosting.id == job_id,
        JobPosting.employer_id == user.id
    ).first()

    if job:
        db.delete(job)
        db.commit()
        request.session["flash_success"] = "Job listing deleted."
    else:
        request.session["flash_error"] = "Job not found."

    return RedirectResponse(url="/employer/dashboard", status_code=302)


# ── Browse Workers ────────────────────────────────────────────────────────────

@router.get("/browse-workers", response_class=HTMLResponse)
async def browse_workers(
    request: Request,
    search: str = "",
    availability: str = "",
    job_type: str = "",
    db: Session = Depends(get_db)
):
    user = get_employer(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    query = db.query(WorkerProfile).join(User, WorkerProfile.worker_id == User.id)

    if availability:
        query = query.filter(WorkerProfile.availability == availability)
    if job_type:
        query = query.filter(WorkerProfile.preferred_job_type == job_type)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            WorkerProfile.skills.ilike(search_term) |
            User.full_name.ilike(search_term) |
            User.location.ilike(search_term)
        )

    workers = query.filter(WorkerProfile.is_available == True).order_by(WorkerProfile.created_at.desc()).all()

    return templates.TemplateResponse(request, "employer/browse_workers.html", {
        "user": user,
        "workers": workers,
        "search": search,
        "availability": availability,
        "job_type": job_type,
    })


# ── Manage Application ────────────────────────────────────────────────────────

@router.post("/application/{app_id}/update")
async def update_application(
    request: Request,
    app_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_employer(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    if status not in ("accepted", "rejected", "pending"):
        request.session["flash_error"] = "Invalid status."
        return RedirectResponse(url="/employer/dashboard", status_code=302)

    # Verify this application belongs to one of the employer's jobs
    application = (
        db.query(JobApplication)
        .join(JobPosting, JobApplication.job_id == JobPosting.id)
        .filter(JobApplication.id == app_id, JobPosting.employer_id == user.id)
        .first()
    )

    if application:
        application.status = status
        db.commit()
        request.session["flash_success"] = f"Application marked as {status}."
    else:
        request.session["flash_error"] = "Application not found."

    return RedirectResponse(url="/employer/dashboard", status_code=302)
