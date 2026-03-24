from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..schemas import FinancialGoalCreate
from ..repositories.goal_repo import goal_repo


class GoalService:
    async def get_user_goals(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
        return await goal_repo.get_by_user(db, user_id=user_id, skip=skip, limit=limit)

    async def create_goal(self, db: AsyncSession, goal_in: FinancialGoalCreate, user_id: int):
        return await goal_repo.create(db, obj_in=goal_in, user_id=user_id)

    async def update_goal(self, db: AsyncSession, goal_id: int, goal_in: FinancialGoalCreate, user_id: int):
        db_g = await goal_repo.get_by_id_and_user(db, goal_id=goal_id, user_id=user_id)
        if not db_g:
            raise HTTPException(status_code=404, detail="Goal not found")
        return await goal_repo.update(db, db_obj=db_g, obj_in=goal_in)

    async def delete_goal(self, db: AsyncSession, goal_id: int, user_id: int):
        db_g = await goal_repo.get_by_id_and_user(db, goal_id=goal_id, user_id=user_id)
        if not db_g:
            raise HTTPException(status_code=404, detail="Goal not found")
        await goal_repo.remove(db, id=db_g.id)
        return {"message": "Goal deleted successfully"}


goal_service = GoalService()
