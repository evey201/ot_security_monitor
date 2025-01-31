from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.services import SessionService
from app.api import require_viewer
from app.db import UserRole
from app.models import SessionInfo
from typing import List

router = APIRouter()



@router.get("/sessions/active", response_model=List[SessionInfo])
async def get_active_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_role: UserRole = Depends(require_viewer)
):
    """Get all active sessions for the current user"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session_service = SessionService(db)
    
    # First validate current session
    user = await session_service.validate_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Get all active sessions
    sessions = await session_service.get_active_sessions(user.id)
    return sessions

@router.post("/sessions/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_role: UserRole = Depends(require_viewer)
):
    """Logout from current session"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session_service = SessionService(db)
    
    if await session_service.invalidate_session(token):
        return {"message": "Logged out successfully"}
    raise HTTPException(status_code=400, detail="Invalid session")

@router.post("/sessions/logout-all")
async def logout_all_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_role: UserRole = Depends(require_viewer)
):
    """Logout from all sessions except current"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session_service = SessionService(db)
    
    # Validate current session
    user = await session_service.validate_session(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Invalidate all other sessions
    await session_service.invalidate_all_sessions(user.id, token)
    return {"message": "Logged out from all other sessions"}