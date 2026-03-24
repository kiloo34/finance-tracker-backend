"""
Admin — User Management Router

All endpoints require the authenticated user to have role='admin'.
Provides full CRUD for user accounts accessible only by administrators.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from .. import database, models
from ..auth.jwt import require_admin

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


# ── Response Schemas ─────────────────────────────────────────────────────────

class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    phone_number: Optional[str]
    role: str
    tier: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class PaginatedUsers(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[AdminUserResponse]


class ChangeRoleRequest(BaseModel):
    role: str  # "admin" or "user"


class ChangeStatusRequest(BaseModel):
    is_active: bool


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/users", response_model=PaginatedUsers)
async def list_all_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    db: AsyncSession = Depends(database.get_db),
    _admin: models.User = Depends(require_admin),
):
    """
    List all users with optional search and role filter.
    Paginated. Admin only.
    """
    query = select(models.User)

    if search:
        like = f"%{search}%"
        query = query.where(
            models.User.username.ilike(like) |
            models.User.email.ilike(like) |
            models.User.phone_number.ilike(like)
        )

    if role in ("admin", "user"):
        query = query.where(models.User.role == role)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    query = query.order_by(models.User.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    users = result.scalars().all()

    return PaginatedUsers(
        total=total,
        page=page,
        per_page=per_page,
        items=[
            AdminUserResponse(
                id=u.id,
                username=u.username,
                email=u.email,
                phone_number=u.phone_number,
                role=u.role.value,
                tier=u.tier.value,
                is_active=u.is_active,
                created_at=u.created_at.isoformat(),
            )
            for u in users
        ],
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(database.get_db),
    _admin: models.User = Depends(require_admin),
):
    """Get a single user's details. Admin only."""
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return AdminUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        role=user.role.value,
        tier=user.tier.value,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
    )


@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: int,
    body: ChangeRoleRequest,
    db: AsyncSession = Depends(database.get_db),
    admin: models.User = Depends(require_admin),
):
    """
    Change a user's role (admin ↔ user).
    An admin cannot demote themselves.
    """
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot change your own role.")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'.")

    user.role = models.UserRole(body.role)
    await db.commit()
    return {"message": f"Role updated to '{body.role}' for user '{user.username}'."}


@router.put("/users/{user_id}/status")
async def change_user_status(
    user_id: int,
    body: ChangeStatusRequest,
    db: AsyncSession = Depends(database.get_db),
    admin: models.User = Depends(require_admin),
):
    """
    Activate or deactivate a user account.
    An admin cannot deactivate themselves.
    """
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot deactivate your own account.")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.is_active = body.is_active
    await db.commit()
    action = "activated" if body.is_active else "deactivated"
    return {"message": f"User '{user.username}' has been {action}."}


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(database.get_db),
    admin: models.User = Depends(require_admin),
):
    """
    Permanently delete a user account and all associated data (cascade).
    An admin cannot delete themselves.
    """
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await db.delete(user)
    await db.commit()
