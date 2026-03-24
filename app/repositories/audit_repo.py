"""
Repository for AuditLog.
Supports writing and reading paginated audit entries for a user.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models import AuditLog


class AuditRepository:

    async def create(
        self,
        db: AsyncSession,
        user_id: int,
        action: str,
        session_id: str | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        ip_address: str | None = None,
        detail: str | None = None,
    ) -> AuditLog:
        """Insert an immutable audit log entry."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            detail=detail,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Return paginated audit logs for a user, newest first."""
        result = await db.execute(
            select(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()


audit_repo = AuditRepository()
