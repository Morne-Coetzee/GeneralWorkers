# GeneralWorkers

A platform connecting general workers with employers in South Africa.

## Tech Stack

- **Backend:** Python FastAPI
- **Templates:** Jinja2 (server-side rendering)
- **Database:** PostgreSQL + SQLAlchemy
- **Auth:** JWT in HTTP-only cookies
- **Styling:** Custom CSS with Poppins font

## Setup

### 1. Clone and install dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

### 3. Create PostgreSQL database

```sql
CREATE DATABASE generalworkers;
```

### 4. Run the application

```bash
uvicorn app.main:app --reload
```

The app will be available at `http://localhost:8000`

## Project Structure

```
GeneralWorkers/
├── app/
│   ├── main.py          # FastAPI entry point
│   ├── database.py      # SQLAlchemy setup
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   ├── routers/         # Route handlers
│   └── templates/       # Jinja2 HTML templates
├── static/              # CSS, JS, images
├── requirements.txt
└── .env.example
```

## User Types

- **Employers** — Post jobs, browse worker profiles, manage applications
- **Workers** — Create profiles, browse jobs, apply to positions

## Color Themes

- **Employer:** Blue (`#0d7ec3`)
- **Worker:** Teal (`#32d0df`)
