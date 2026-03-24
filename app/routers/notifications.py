from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app import schemas
from app.auth.jwt import get_current_user
from app.models import User
from app.repositories.notification_repo import NotificationRepository
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    repo = NotificationRepository(db)
    return NotificationService(repo)


@router.get("/", response_model=List[schemas.NotificationResponse])
async def get_my_notifications(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    return await service.get_user_notifications(current_user.id, skip=skip, limit=limit)


@router.get("/unread-count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    count = await service.count_unread(current_user.id)
    return {"unread": count}


@router.put("/{notification_id}/read", response_model=schemas.NotificationResponse)
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    return await service.mark_as_read(notification_id, current_user.id)


@router.put("/read-all", response_model=dict)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service)
):
    return await service.mark_all_as_read(current_user.id)
