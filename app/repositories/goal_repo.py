from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repo import CRUDBase
from ..models import FinancialGoal
from ..schemas import FinancialGoalCreate

class RepositoryFinancialGoal(CRUDBase[FinancialGoal, FinancialGoalCreate, FinancialGoalCreate]):
    async def get_by_user(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[FinancialGoal]:
        result = await db.execute(select(self.model).filter(self.model.user_id == user_id).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_by_id_and_user(self, db: AsyncSession, goal_id: int, user_id: int) -> FinancialGoal | None:
        result = await db.execute(select(self.model).filter(self.model.id == goal_id, self.model.user_id == user_id))
        return result.scalars().first()

goal_repo = RepositoryFinancialGoal(FinancialGoal)
