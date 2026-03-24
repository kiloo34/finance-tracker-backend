from typing import List
from fastapi import HTTPException
from app.repositories.notification_repo import NotificationRepository
from app.models import Notification, NotificationStatus


class NotificationService:
    def __init__(self, notification_repo: NotificationRepository):
        self.repo = notification_repo

    async def get_user_notifications(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Notification]:
        return await self.repo.get_by_user(user_id, skip=skip, limit=limit)

    async def count_unread(self, user_id: int) -> int:
        return await self.repo.count_unread(user_id)

    async def mark_as_read(self, notification_id: int, user_id: int) -> Notification:
        notification = await self.repo.get(self.repo.db, id=notification_id)
        if not notification or notification.user_id != user_id:
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.status = NotificationStatus.read
        await self.repo.db.commit()
        await self.repo.db.refresh(notification)
        return notification

    async def mark_all_as_read(self, user_id: int) -> dict:
        count = await self.repo.mark_all_as_read(user_id)
        return {"message": f"Marked {count} notifications as read"}

    async def create_notification(self, user_id: int, title: str, message: str) -> None:
        """Background-safe helper: creates a notification for the user. Can be called from BackgroundTasks."""
        from app.models import Notification, NotificationStatus
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            status=NotificationStatus.unread
        )
        self.repo.db.add(notif)
        await self.repo.db.commit()
