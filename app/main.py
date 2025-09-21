from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from .database import SessionLocal, engine
from . import models
from .models import Base, User, Post # Make sure to import Post here
from .auth import get_password_hash, verify_password, create_access_token, get_current_user
from .routers import issues, users, admin, notifications, social, profile



# Create tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Civic Issue Reporting System",
    description="A comprehensive system for reporting and managing civic issues",
    version="1.0.0"
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(issues.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(social.router)
app.include_router(profile.router)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserSignup(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    """
    This is the main feed page. It gets all posts from the DB
    and renders the feed.html template.
    """
    try:
        # Fetch all posts from the database, newest first
        posts = db.query(models.Post).order_by(models.Post.id.desc()).all()
        
        # Return the HTML template, passing in the posts data
        return templates.TemplateResponse("feed.html", {"request": request, "posts": posts})
    except Exception as e:
        # If there's an error, return a simple HTML page
        return HTMLResponse(f"""
        <html>
        <head><title>Civic Backend</title></head>
        <body>
            <h1>Civic Issue Reporting System</h1>
            <p>Server is running! Error: {str(e)}</p>
            <p><a href="/docs">API Documentation</a></p>
        </body>
        </html>
        """)

@app.get("/test")
def test_endpoint():
    return {"message": "Server is working!", "status": "ok"}

@app.post("/signup")
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    """Register a new user"""
    user = db.query(User).filter(User.email == user_data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")
    
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@app.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }
