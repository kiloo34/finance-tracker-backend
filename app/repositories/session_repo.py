"""
Repository for UserSession management.
Handles session creation, lookup, revocation, and last-seen updates.
"""
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from ..models import UserSession, SessionStatus


class SessionRepository:

    async def create(
        self,
        db: AsyncSession,
        session_id: str,
        user_id: int,
        ip_address: str,
        user_agent: str,
        device_hint: str,
    ) -> UserSession:
        """Insert a new active session record."""
        session = UserSession(
            id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_hint=device_hint,
            status=SessionStatus.active,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_by_id(self, db: AsyncSession, session_id: str) -> UserSession | None:
        """Fetch a single session by its ID (the JWT jti)."""
        result = await db.execute(
            select(UserSession).filter(UserSession.id == session_id)
        )
        return result.scalars().first()

    async def get_active_by_user(self, db: AsyncSession, user_id: int) -> list[UserSession]:
        """Return all active sessions for a user, newest first."""
        result = await db.execute(
            select(UserSession)
            .filter(UserSession.user_id == user_id, UserSession.status == SessionStatus.active)
            .order_by(UserSession.created_at.desc())
        )
        return result.scalars().all()

    async def revoke(self, db: AsyncSession, session_id: str, user_id: int) -> bool:
        """Revoke a session by ID, only if it belongs to user_id. Returns True on success."""
        result = await db.execute(
            update(UserSession)
            .where(UserSession.id == session_id, UserSession.user_id == user_id)
            .values(
                status=SessionStatus.revoked,
                revoked_at=datetime.now(timezone.utc)
            )
            .returning(UserSession.id)
        )
        await db.commit()
        return result.fetchone() is not None

    async def revoke_all(self, db: AsyncSession, user_id: int, except_session_id: str | None = None) -> int:
        """Revoke all active sessions for a user. Optionally exclude the current session."""
        stmt = update(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.status == SessionStatus.active
        )
        if except_session_id:
            stmt = stmt.where(UserSession.id != except_session_id)
        stmt = stmt.values(
            status=SessionStatus.revoked,
            revoked_at=datetime.now(timezone.utc)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    async def touch(self, db: AsyncSession, session_id: str) -> None:
        """Update last_seen_at to current timestamp (called on every authenticated request)."""
        await db.execute(
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(last_seen_at=datetime.now(timezone.utc))
        )
        await db.commit()


session_repo = SessionRepository()
