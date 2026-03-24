"""
Audit logging helper — call this from any router via BackgroundTasks
so audit writes never block the HTTP response.

Usage:
    from app.core.audit import log_action
    background_tasks.add_task(log_action, db, user_id=..., action="transaction.create", ...)
"""
import json
from sqlalchemy.ext.asyncio import AsyncSession
from ..repositories.audit_repo import audit_repo


async def log_action(
    db: AsyncSession,
    *,
    user_id: int,
    action: str,
    session_id: str | None = None,
    resource_type: str | None = None,
    resource_id: int | None = None,
    ip_address: str | None = None,
    detail: dict | None = None,
) -> None:
    """
    Fire-and-forget audit log writer.

    Always call via BackgroundTasks.add_task() to avoid blocking the response.
    """
    detail_str = json.dumps(detail, default=str) if detail else None
    await audit_repo.create(
        db=db,
        user_id=user_id,
        action=action,
        session_id=session_id,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        detail=detail_str,
    )
