import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app.database import engine, Base, SessionLocal
from app.routers import auth, employer, worker

load_dotenv()

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

# Seed default skills
SKILLS = [
    "Painting", "Plastering", "Tiling", "Carpentry", "Plumbing",
    "Electrical Work", "Bricklaying", "Welding", "Gardening & Landscaping",
    "Cleaning", "Driving (Code 8)", "Driving (Code 10)", "Driving (Code 14)",
    "Moving & Removals", "Construction & Labouring", "Roofing", "Paving",
    "Waterproofing", "Security", "Domestic Work", "Cooking & Catering",
    "Childcare", "Elder Care", "Car Washing & Valeting", "Pest Control",
    "Pool Maintenance", "Fencing", "Excavation & Digging", "Waste Removal",
    "General Maintenance",
]

def seed_skills():
    from app.models import Skill
    db = SessionLocal()
    try:
        if db.query(Skill).count() == 0:
            db.bulk_insert_mappings(Skill, [{"name": s} for s in SKILLS])
            db.commit()
    finally:
        db.close()

seed_skills()

app = FastAPI(title="GeneralWorkers", description="Connecting workers with employers")

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "static")),
    name="static",
)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

app.include_router(auth.router)
app.include_router(employer.router)
app.include_router(worker.router)

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")


@app.get("/")
async def landing(request: Request):
    user_id = request.session.get("user_id")
    user_type = request.session.get("user_type")
    if user_id and user_type == "employer":
        return RedirectResponse(url="/employer/dashboard", status_code=302)
    if user_id and user_type == "worker":
        return RedirectResponse(url="/worker/dashboard", status_code=302)
    return templates.TemplateResponse(request, "landing.html")
