from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..schemas import BudgetCreate
from ..repositories.budget_repo import budget_repo
from ..repositories.category_repo import category_repo

class BudgetService:
    async def get_user_budgets(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
        # We also want to eager load or attach the category details in a real scenario
        # But for now returning the base schema which can be hydrated on the frontend 
        # using the existing categories endpoint
        return await budget_repo.get_by_user(db, user_id=user_id, skip=skip, limit=limit)

    async def create_budget(self, db: AsyncSession, budget_in: BudgetCreate, user_id: int):
        # 1. Verify that the requested category exists and belongs to the user
        category = await category_repo.get_by_id_and_user(db, category_id=budget_in.category_id, user_id=user_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found or access denied")
        
        # 2. Prevent duplicate budgets for the same category on the same month/year
        existing = await budget_repo.get_by_category_and_period(db, user_id=user_id, category_id=budget_in.category_id, month=budget_in.month, year=budget_in.year)
        if existing:
            raise HTTPException(status_code=400, detail="A budget already exists for this category in the specified period.")

        return await budget_repo.create(db, obj_in=budget_in, user_id=user_id)

    async def update_budget(self, db: AsyncSession, budget_id: int, budget_in: BudgetCreate, user_id: int):
        # 1. Ensure the budget exists
        db_b = await budget_repo.get_by_id_and_user(db, budget_id=budget_id, user_id=user_id)
        if not db_b:
            raise HTTPException(status_code=404, detail="Budget not found")
            
        # 2. Check category validation
        if db_b.category_id != budget_in.category_id:
            category = await category_repo.get_by_id_and_user(db, category_id=budget_in.category_id, user_id=user_id)
            if not category:
                raise HTTPException(status_code=404, detail="Category not found or access denied")

        # 3. Prevent conflict if modifying period
        if (db_b.month != budget_in.month or db_b.year != budget_in.year or db_b.category_id != budget_in.category_id):
            conflict = await budget_repo.get_by_category_and_period(db, user_id=user_id, category_id=budget_in.category_id, month=budget_in.month, year=budget_in.year)
            if conflict and conflict.id != budget_id:
               raise HTTPException(status_code=400, detail="Another budget already exists for this category in the specified period.")

        return await budget_repo.update(db, db_obj=db_b, obj_in=budget_in)

    async def delete_budget(self, db: AsyncSession, budget_id: int, user_id: int):
        db_b = await budget_repo.get_by_id_and_user(db, budget_id=budget_id, user_id=user_id)
        if not db_b:
            raise HTTPException(status_code=404, detail="Budget not found")
        await budget_repo.remove(db, id=db_b.id)
        return {"message": "Budget deleted successfully"}

budget_service = BudgetService()
