import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app.database import engine, Base
from app.routers import auth, employer, worker

load_dotenv()

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GeneralWorkers", description="Connecting workers with employers")

# Session middleware (must be added before routes)
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Static files
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "static")),
    name="static",
)

# Templates
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Routers
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
