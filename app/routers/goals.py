from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, database, models
from ..auth.jwt import get_current_user, get_session_id_from_token, oauth2_scheme
from ..services.goal_service import goal_service
from ..core.audit import log_action

router = APIRouter(
    prefix="/goals",
    tags=["Financial Goals"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.FinancialGoalResponse])
async def read_goals(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    return await goal_service.get_user_goals(db, user_id=current_user.id, skip=skip, limit=limit)


@router.post("/", response_model=schemas.FinancialGoalResponse)
async def create_goal(
    goal: schemas.FinancialGoalCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    result = await goal_service.create_goal(db=db, goal_in=goal, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="goal.create",
        session_id=session_id, resource_type="FinancialGoal", resource_id=result.id,
        ip_address=request.client.host if request.client else None,
        detail={"name": goal.name, "target_amount": goal.target_amount},
    )
    return result


@router.put("/{goal_id}", response_model=schemas.FinancialGoalResponse)
async def update_goal(
    goal_id: int,
    goal: schemas.FinancialGoalCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    result = await goal_service.update_goal(db, goal_id=goal_id, goal_in=goal, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="goal.update",
        session_id=session_id, resource_type="FinancialGoal", resource_id=goal_id,
        ip_address=request.client.host if request.client else None,
        detail={"current_amount": goal.current_amount, "status": goal.status},
    )
    return result


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    result = await goal_service.delete_goal(db, goal_id=goal_id, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="goal.delete",
        session_id=session_id, resource_type="FinancialGoal", resource_id=goal_id,
        ip_address=request.client.host if request.client else None,
    )
    return result
