from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User
from app.config import settings
from typing import Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, redirect_uri: Optional[str] = None):
    """Display the login page."""
    return templates.TemplateResponse("login.html", {
        "request": request,
        "redirect_uri": redirect_uri,
        "alert_auto_hide_seconds": settings.alert_auto_hide_seconds,
        "form_loading_timeout_seconds": settings.form_loading_timeout_seconds
    })


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    redirect_uri: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Handle user login."""
    user = AuthService.authenticate_user(db, email, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password",
            "redirect_uri": redirect_uri,
            "alert_auto_hide_seconds": settings.alert_auto_hide_seconds,
            "form_loading_timeout_seconds": settings.form_loading_timeout_seconds
        })
    
    # Store user session (simplified - in production use proper session management)
    response = RedirectResponse(url=redirect_uri or "/", status_code=302)
    response.set_cookie(key="user_id", value=str(user.id), httponly=True)
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Display the registration page."""
    return templates.TemplateResponse("register.html", {
        "request": request,
        "alert_auto_hide_seconds": settings.alert_auto_hide_seconds,
        "form_loading_timeout_seconds": settings.form_loading_timeout_seconds
    })


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle user registration."""
    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Passwords do not match",
            "alert_auto_hide_seconds": settings.alert_auto_hide_seconds,
            "form_loading_timeout_seconds": settings.form_loading_timeout_seconds
        })
    
    # Check if user already exists
    existing_user = AuthService.get_user_by_email(db, email)
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Email already registered",
            "alert_auto_hide_seconds": settings.alert_auto_hide_seconds,
            "form_loading_timeout_seconds": settings.form_loading_timeout_seconds
        })
    
    # Create new user
    try:
        user = AuthService.create_user(db, email, password, first_name, last_name)
        response = RedirectResponse(url="/login", status_code=302)
        return response
    except Exception as e:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Registration failed. Please try again.",
            "alert_auto_hide_seconds": settings.alert_auto_hide_seconds,
            "form_loading_timeout_seconds": settings.form_loading_timeout_seconds
        })


@router.get("/logout")
async def logout():
    """Handle user logout."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(key="user_id")
    return response


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get the current authenticated user from session."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    
    try:
        return AuthService.get_user_by_id(db, int(user_id))
    except (ValueError, TypeError):
        return None
