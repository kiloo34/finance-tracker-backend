"""
Session management router.
Allows users to view active sessions and revoke them (remote logout).
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from .. import database, models, schemas
from ..auth import jwt
from ..repositories.session_repo import session_repo
from ..core.audit import log_action

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.get("/", response_model=list[schemas.UserSessionResponse])
async def get_my_sessions(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user),
):
    """List all active login sessions for the current user."""
    return await session_repo.get_active_by_user(db=db, user_id=current_user.id)


@router.delete("/{session_id}")
async def revoke_session(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user),
    token: str = Depends(jwt.oauth2_scheme),
):
    """
    Revoke a specific session by ID (remote logout from one device).
    Only the owning user can revoke their own sessions.
    """
    success = await session_repo.revoke(
        db=db, session_id=session_id, user_id=current_user.id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or already revoked.")

    # Log the audit event asynchronously
    current_session_id = await jwt.get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id,
        action="session.revoke",
        session_id=current_session_id,
        resource_type="UserSession",
        resource_id=None,
        detail={"revoked_session_id": session_id},
    )
    return {"message": "Session successfully revoked.", "session_id": session_id}


@router.delete("/")
async def revoke_all_other_sessions(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user),
    token: str = Depends(jwt.oauth2_scheme),
):
    """Revoke ALL other active sessions — logs user out from every other device."""
    current_session_id = await jwt.get_session_id_from_token(token=token)
    count = await session_repo.revoke_all(
        db=db,
        user_id=current_user.id,
        except_session_id=current_session_id or "",
    )
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id,
        action="session.revoke_all",
        session_id=current_session_id,
        detail={"revoked_count": count},
    )
    return {"message": f"Revoked {count} other active session(s).", "revoked_count": count}
