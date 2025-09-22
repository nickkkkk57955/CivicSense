# In app/routers/web_auth_router.py
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from .. import models, auth, database

router = APIRouter(tags=["Web Auth"])

@router.post("/signup-form", response_class=HTMLResponse)
def signup_form(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        # You can add error handling here if you want
        return HTMLResponse("Email already exists", status_code=400)

    hashed = auth.get_password_hash(password)
    user = models.User(name=name, email=email, hashed_password=hashed)
    db.add(user)
    db.commit()

    # Redirect to the login page after successful signup
    return HTMLResponse("<script>window.location.href = '/login';</script>")

@router.post("/login-form", response_class=HTMLResponse)
def login_form(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == username).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return HTMLResponse("Invalid credentials", status_code=400)

    token = auth.create_access_token({"sub": user.email})

    # This script saves the token in the browser and redirects to the homepage
    return HTMLResponse(f"""
    <script>
        localStorage.setItem('access_token', '{token}');
        window.location.href = '/';
    </script>
    """)