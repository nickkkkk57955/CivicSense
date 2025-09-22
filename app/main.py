# In app/main.py
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from . import models
from .database import engine, get_db
from .routers import auth_router, issues, web_auth_router, social, profile, admin, notifications, users

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Civic Issue Reporting System")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include your API routers
app.include_router(auth_router.router)
app.include_router(issues.router)
app.include_router(social.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(users.router)

# Include your WEB FORM router
app.include_router(web_auth_router.router)

# --- Routes to SERVE HTML PAGES ---
@app.get("/", response_class=HTMLResponse)
def serve_feed(request: Request, db: Session = Depends(get_db)):
    issues = db.query(models.Issue).order_by(models.Issue.id.desc()).all()
    return templates.TemplateResponse("feed.html", {"request": request, "issues": issues})

@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/report", response_class=HTMLResponse)
def report_page(request: Request):
    return templates.TemplateResponse("report_issue.html", {"request": request})