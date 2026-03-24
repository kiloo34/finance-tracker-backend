from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..schemas import CategoryCreate
from ..repositories.category_repo import category_repo


class CategoryService:
    async def get_user_categories(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 200):
        return await category_repo.get_by_user(db, user_id=user_id, skip=skip, limit=limit)

    async def create_category(self, db: AsyncSession, category_in: CategoryCreate, user_id: int):
        return await category_repo.create(db, obj_in=category_in, user_id=user_id)

    async def update_category(self, db: AsyncSession, category_id: int, category_in: CategoryCreate, user_id: int):
        db_c = await category_repo.get_by_id_and_user(db, category_id=category_id, user_id=user_id)
        if not db_c:
            raise HTTPException(status_code=404, detail="Category not found")
        return await category_repo.update(db, db_obj=db_c, obj_in=category_in)

    async def delete_category(self, db: AsyncSession, category_id: int, user_id: int):
        db_c = await category_repo.get_by_id_and_user(db, category_id=category_id, user_id=user_id)
        if not db_c:
            raise HTTPException(status_code=404, detail="Category not found")
        await category_repo.remove(db, id=db_c.id)
        return {"message": "Category deleted successfully"}


category_service = CategoryService()
