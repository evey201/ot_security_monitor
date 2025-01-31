from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.db import User, UserRole
from app.core import verify_password, get_password_hash, create_access_token
from app.models import UserCreate
from datetime import timedelta
from app.core import get_settings
from jose import JWTError, jwt

settings = get_settings()

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate_user(
        self, 
        username: str, 
        password: str
    ):
        """Authenticate a user"""
        user = await self.get_user_by_username(username)
        
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        return user

    async def create_user(
        self, 
        user_create: UserCreate
    ) -> User:
        """Create a new user"""
        # Check if user exists
        query = select(User).where(
            (User.email == user_create.email) | 
            (User.username == user_create.username)
        )
        result = await self.db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Username or email already registered"
            )

        # Create new user
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            hashed_password=get_password_hash(user_create.password),
            role=user_create.role
        )
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user

    async def get_user_by_username(
        self, 
        username: str
    ) -> User:
        """Get a user by username"""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    def create_user_token(
        self, 
        user: User
    ) -> dict:
        """Create access token for user"""
        access_token_expires = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={
                "sub": user.username,
                "role": user.role.value
            },
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    async def verify_current_password(
        self, 
        username: str, 
        password: str
    ) -> bool:
        """Verify user's current password"""
        user = await self.get_user_by_username(username)
        if not user:
            return False
        return verify_password(password, user.hashed_password)

    async def update_password(
        self, 
        username: str, 
        new_password: str
    ):
        """Update user's password"""
        user = await self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
            
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()

    async def reset_password(
        self, 
        username: str, 
        new_password: str
    ):
        """Reset user's password (admin function)"""
        user = await self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
            
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()

    async def verify_admin_token(
        self, 
        token: str
    ) -> bool:
        """Verify if the token belongs to an admin user"""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            return payload.get("role") == UserRole.ADMIN.value
        except JWTError:
            return False
