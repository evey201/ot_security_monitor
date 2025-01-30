from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import get_current_user_role
from app.db import UserRole
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def require_roles(allowed_roles: List[UserRole]):
    """Dependency for role-based access control"""
    async def role_checker(token: str = Depends(oauth2_scheme)):
        user_role = await get_current_user_role(token)
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return user_role
    return role_checker

# Convenience dependencies for common role requirements
require_admin = require_roles([UserRole.ADMIN])
require_operator = require_roles([UserRole.ADMIN, UserRole.OPERATOR])
require_viewer = require_roles([UserRole.ADMIN, UserRole.OPERATOR, UserRole.VIEWER])