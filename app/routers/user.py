from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.routers.auth import get_current_user
from app.models.user import User
from typing import Optional

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
async def get_current_user_info(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current user information."""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "created_at": user.created_at
    }


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get user by ID (admin only or self)."""
    current_user = get_current_user(request, db)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # For now, users can only access their own information
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    user = AuthService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "created_at": user.created_at
    }
