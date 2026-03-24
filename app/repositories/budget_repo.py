from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repo import CRUDBase
from ..models import Budget
from ..schemas import BudgetCreate

class RepositoryBudget(CRUDBase[Budget, BudgetCreate, BudgetCreate]):
    async def get_by_user(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Budget]:
        result = await db.execute(select(self.model).filter(self.model.user_id == user_id).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_by_id_and_user(self, db: AsyncSession, budget_id: int, user_id: int) -> Budget | None:
        result = await db.execute(select(self.model).filter(self.model.id == budget_id, self.model.user_id == user_id))
        return result.scalars().first()
        
    async def get_by_category_and_period(self, db: AsyncSession, user_id: int, category_id: int, month: int, year: int) -> Budget | None:
        result = await db.execute(select(self.model).filter(
            self.model.user_id == user_id,
            self.model.category_id == category_id,
            self.model.month == month,
            self.model.year == year
        ))
        return result.scalars().first()

budget_repo = RepositoryBudget(Budget)
