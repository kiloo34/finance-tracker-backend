from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, database, models
from ..auth.jwt import get_current_user, require_admin, get_session_id_from_token, oauth2_scheme
from ..services.category_service import category_service
from ..core.audit import log_action

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.CategoryWithSub])
async def read_categories(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    # Fetch root categories (parent_id is null) for the user and their subcategories
    result = await db.execute(
        select(models.Category)
        .filter(models.Category.user_id == current_user.id, models.Category.parent_id == None)
        .options(selectinload(models.Category.subcategories))
    )
    return result.scalars().all()


@router.post("/", response_model=schemas.CategoryResponse)
async def create_category(
    category: schemas.CategoryCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(require_admin),
    token: str = Depends(oauth2_scheme),
):
    result = await category_service.create_category(db=db, category_in=category, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="category.create",
        session_id=session_id, resource_type="Category", resource_id=result.id,
        ip_address=request.client.host if request.client else None,
        detail={"name": category.name, "type": category.type},
    )
    return result


@router.put("/{category_id}", response_model=schemas.CategoryResponse)
async def update_category(
    category_id: int,
    category: schemas.CategoryCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(require_admin),
    token: str = Depends(oauth2_scheme),
):
    result = await category_service.update_category(db, category_id=category_id, category_in=category, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="category.update",
        session_id=session_id, resource_type="Category", resource_id=category_id,
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(require_admin),
    token: str = Depends(oauth2_scheme),
):
    result = await category_service.delete_category(db, category_id=category_id, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="category.delete",
        session_id=session_id, resource_type="Category", resource_id=category_id,
        ip_address=request.client.host if request.client else None,
    )
    return result
