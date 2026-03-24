from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.repositories.base_repo import CRUDBase
from app.models import Notification, NotificationStatus


# Use a small dummy schema for CreateSchemaType and UpdateSchemaType since
# NotificationRepository manages creation directly via model instantiation.
class _NotifCreate:
    def model_dump(self) -> dict:
        return {}


class NotificationRepository(CRUDBase[Notification, _NotifCreate, _NotifCreate]):
    def __init__(self, db: AsyncSession):
        super().__init__(Notification)
        self.db = db

    async def get_by_user(self, user_id: int, skip: int = 0, limit: int = 50) -> List[Notification]:
        result = await self.db.execute(
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count_unread(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(self.model.id))
            .filter(self.model.user_id == user_id, self.model.status == NotificationStatus.unread)
        )
        return result.scalar() or 0

    async def mark_all_as_read(self, user_id: int) -> int:
        stmt = update(self.model).filter(
            self.model.user_id == user_id,
            self.model.status == NotificationStatus.unread
        ).values(status=NotificationStatus.read)
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount
