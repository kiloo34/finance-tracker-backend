"""
Audit log router.
Users can view their own activity history — who did what, from where, and when.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from .. import database, models, schemas
from ..auth import jwt
from ..repositories.audit_repo import audit_repo

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("/", response_model=list[schemas.AuditLogResponse])
async def get_my_audit_log(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user),
):
    """
    Retrieve paginated audit history for the current user.

    Returns actions in reverse-chronological order (newest first).
    Use `limit` and `offset` for pagination.
    """
    return await audit_repo.get_by_user(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
