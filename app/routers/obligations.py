from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, database, models
from ..auth.jwt import get_current_user, get_session_id_from_token, oauth2_scheme
from ..services.obligation_service import obligation_service
from ..core.audit import log_action

router = APIRouter(
    prefix="/obligations",
    tags=["Obligations"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=List[schemas.ObligationResponse])
async def read_obligations(
    type: models.ObligationType | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await obligation_service.get_user_obligations(db, user_id=current_user.id, type=type, skip=skip, limit=limit)

@router.post("", response_model=schemas.ObligationResponse)
async def create_obligation(
    obligation: schemas.ObligationCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    result = await obligation_service.create_obligation(db=db, obj_in=obligation, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action=f"obligation.create.{obligation.type}",
        session_id=session_id, resource_type="Obligation", resource_id=result.id,
        ip_address=request.client.host if request.client else None,
        detail={"contact_name": obligation.contact_name, "amount": float(obligation.amount)},
    )
    return result

@router.put("/{obligation_id}", response_model=schemas.ObligationResponse)
async def update_obligation(
    obligation_id: int,
    obligation: schemas.ObligationCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    result = await obligation_service.update_obligation(db, obligation_id=obligation_id, obj_in=obligation, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action=f"obligation.update.{obligation.type}",
        session_id=session_id, resource_type="Obligation", resource_id=obligation_id,
        ip_address=request.client.host if request.client else None,
        detail={"status": obligation.status, "remaining_amount": float(obligation.remaining_amount)},
    )
    return result

@router.delete("/{obligation_id}")
async def delete_obligation(
    obligation_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    result = await obligation_service.delete_obligation(db, obligation_id=obligation_id, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="obligation.delete",
        session_id=session_id, resource_type="Obligation", resource_id=obligation_id,
        ip_address=request.client.host if request.client else None,
    )
    return result
