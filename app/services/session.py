from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete
from datetime import datetime, timedelta, timezone
from app.db import Session, User
from typing import Optional, List
from fastapi import Request

class SessionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        user_id: int,
        token: str,
        request: Request
    ) -> Session:
        """Create a new session"""
        # Get device info from request headers
        user_agent = request.headers.get("user-agent", "")
        client_ip = request.client.host if request.client else None
        
        # Create session with 30-day expiry
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)
        
        session = Session(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            device_info=user_agent,
            ip_address=client_ip,
            is_active=True
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session

    async def get_active_sessions(
        self,
        user_id: int
    ) -> List[Session]:
        """Get all active sessions for a user"""
        query = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.is_active == True,  # noqa: E712
                Session.expires_at > datetime.now(timezone.utc)
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def invalidate_session(
        self,
        token: str
    ) -> bool:
        """Invalidate a specific session"""
        query = select(Session).where(Session.token == token)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            session.is_active = False
            await self.db.commit()
            return True
        return False

    async def invalidate_all_sessions(
        self,
        user_id: int,
        current_token: Optional[str] = None
    ):
        """Invalidate all sessions for a user except current"""
        query = select(Session).where(
            and_(
                Session.user_id == user_id,
                Session.is_active == True,  # noqa: E712
                Session.token != current_token if current_token else True
            )
        )
        result = await self.db.execute(query)
        sessions = result.scalars().all()
        
        for session in sessions:
            session.is_active = False
        
        await self.db.commit()

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        query = delete(Session).where(
            or_(
                Session.expires_at < datetime.now(timezone.utc),
                Session.is_active == False  # noqa: E712
            )
        )
        await self.db.execute(query)
        await self.db.commit()

    async def validate_session(
        self,
        token: str
    ) -> Optional[User]:
        """Validate a session and return the user"""
        query = select(Session).where(
            and_(
                Session.token == token,
                Session.is_active == True,  # noqa: E712
                Session.expires_at > datetime.now(timezone.utc)
            )
        ).join(Session.user)
        
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if session:
            # Update last activity
            session.last_activity = datetime.now(timezone.utc)
            await self.db.commit()
            return session.user
        
        return None