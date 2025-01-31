from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.services import AuthService
from app.api import require_viewer
from app.models import PasswordReset, PasswordChange

router = APIRouter(tags="Password Change/Reset")


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_viewer)  # This ensures user is authenticated
):
    """Change password for logged-in user"""
    auth_service = AuthService(db)
    
    # Verify old password
    if not await auth_service.verify_current_password(current_user.username, password_data.old_password):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )
    
    # Update password
    await auth_service.update_password(current_user.username, password_data.new_password)
    return {"message": "Password updated successfully"}

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """Reset password (admin functionality)"""
    auth_service = AuthService(db)
    
    # Check if it's an admin request
    if reset_data.admin_token:
        # Verify admin token
        if not await auth_service.verify_admin_token(reset_data.admin_token):
            raise HTTPException(
                status_code=403,
                detail="Invalid admin token"
            )
    else:
        raise HTTPException(
            status_code=403,
            detail="Admin token required for password reset"
        )
    
    # Reset the password
    try:
        await auth_service.reset_password(reset_data.username, reset_data.new_password)
        return {"message": "Password reset successful"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))