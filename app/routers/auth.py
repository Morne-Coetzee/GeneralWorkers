import os
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional

from app.database import get_db
from app.models import User

router = APIRouter(tags=["auth"])

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def require_employer(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user or user.user_type != "employer":
        raise Exception("Not authorized")
    return user


def require_worker(request: Request, db: Session = Depends(get_db)) -> User:
    user = get_current_user(request, db)
    if not user or user.user_type != "worker":
        raise Exception("Not authorized")
    return user


# ── Register ──────────────────────────────────────────────────────────────────

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user_type: Optional[str] = None):
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "user_type": user_type or "", "error": request.session.pop("flash_error", None)}
    )


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    full_name: str = Form(...),
    user_type: str = Form(...),
    phone: str = Form(""),
    location: str = Form(""),
    db: Session = Depends(get_db)
):
    # Validation
    if password != confirm_password:
        request.session["flash_error"] = "Passwords do not match."
        return RedirectResponse(url=f"/register?user_type={user_type}", status_code=302)

    if len(password) < 6:
        request.session["flash_error"] = "Password must be at least 6 characters."
        return RedirectResponse(url=f"/register?user_type={user_type}", status_code=302)

    if user_type not in ("employer", "worker"):
        request.session["flash_error"] = "Invalid user type."
        return RedirectResponse(url="/register", status_code=302)

    # Check duplicate email
    existing = db.query(User).filter(User.email == email.lower()).first()
    if existing:
        request.session["flash_error"] = "An account with that email already exists."
        return RedirectResponse(url=f"/register?user_type={user_type}", status_code=302)

    user = User(
        email=email.lower().strip(),
        password_hash=hash_password(password),
        user_type=user_type,
        full_name=full_name.strip(),
        phone=phone.strip() or None,
        location=location.strip() or None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Log them in immediately
    request.session["user_id"] = user.id
    request.session["user_type"] = user.user_type
    request.session["full_name"] = user.full_name

    if user.user_type == "employer":
        return RedirectResponse(url="/employer/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/worker/profile", status_code=302)


# ── Login ─────────────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "error": request.session.pop("flash_error", None)}
    )


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        request.session["flash_error"] = "Invalid email or password."
        return RedirectResponse(url="/login", status_code=302)

    request.session["user_id"] = user.id
    request.session["user_type"] = user.user_type
    request.session["full_name"] = user.full_name

    if user.user_type == "employer":
        return RedirectResponse(url="/employer/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/worker/dashboard", status_code=302)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=302)
