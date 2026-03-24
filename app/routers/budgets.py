from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, database, models
from ..auth import jwt
from ..services.budget_service import budget_service
from ..core.audit import log_action

router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
)


@router.get("/", response_model=List[schemas.BudgetResponse])
async def read_budgets(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user)
):
    """
    Retrieve all budgets for the currently authenticated user.
    """
    return await budget_service.get_user_budgets(db, user_id=current_user.id, skip=skip, limit=limit)


@router.post("/", response_model=schemas.BudgetResponse)
async def create_budget(
    budget: schemas.BudgetCreate,
    background_tasks: BackgroundTasks,
    request: getattr(__import__('fastapi'), 'Request'),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user),
    token: str = Depends(jwt.oauth2_scheme)
):
    """
    Create a new budget limit for a category in a specific month and year.
    """
    new_budget = await budget_service.create_budget(db, budget_in=budget, user_id=current_user.id)
    
    # Audit log
    session_id = await jwt.get_session_id_from_token(token)
    background_tasks.add_task(
        log_action,
        db=db,
        user_id=current_user.id,
        action="budget.create",
        session_id=session_id,
        resource_type="Budget",
        resource_id=new_budget.id,
        ip=request.client.host if request.client else None,
        detail=f"Created budget for category {new_budget.category_id} limit {new_budget.amount_limit}"
    )
    return new_budget


@router.put("/{budget_id}", response_model=schemas.BudgetResponse)
async def update_budget(
    budget_id: int,
    budget: schemas.BudgetCreate,
    background_tasks: BackgroundTasks,
    request: getattr(__import__('fastapi'), 'Request'),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user),
    token: str = Depends(jwt.oauth2_scheme)
):
    """
    Update an existing budget.
    """
    updated_budget = await budget_service.update_budget(
        db, budget_id=budget_id, budget_in=budget, user_id=current_user.id
    )
    
    session_id = await jwt.get_session_id_from_token(token)
    background_tasks.add_task(
        log_action,
        db=db,
        user_id=current_user.id,
        action="budget.update",
        session_id=session_id,
        resource_type="Budget",
        resource_id=updated_budget.id,
        ip=request.client.host if request.client else None,
        detail=f"Updated budget limit to {updated_budget.amount_limit}"
    )
    return updated_budget


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    background_tasks: BackgroundTasks,
    request: getattr(__import__('fastapi'), 'Request'),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user),
    token: str = Depends(jwt.oauth2_scheme)
):
    """
    Delete a budget.
    """
    result = await budget_service.delete_budget(db, budget_id=budget_id, user_id=current_user.id)
    
    session_id = await jwt.get_session_id_from_token(token)
    background_tasks.add_task(
        log_action,
        db=db,
        user_id=current_user.id,
        action="budget.delete",
        session_id=session_id,
        resource_type="Budget",
        resource_id=budget_id,
        ip=request.client.host if request.client else None,
        detail=f"Deleted budget {budget_id}"
    )
    return result
