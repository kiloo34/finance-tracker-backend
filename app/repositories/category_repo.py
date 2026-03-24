from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repo import CRUDBase
from ..models import Category
from ..schemas import CategoryCreate

class RepositoryCategory(CRUDBase[Category, CategoryCreate, CategoryCreate]):
    async def get_by_user(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 200) -> List[Category]:
        result = await db.execute(select(self.model).filter(self.model.user_id == user_id).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_by_id_and_user(self, db: AsyncSession, category_id: int, user_id: int) -> Category | None:
        result = await db.execute(select(self.model).filter(self.model.id == category_id, self.model.user_id == user_id))
        return result.scalars().first()

category_repo = RepositoryCategory(Category)
