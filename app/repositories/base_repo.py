from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from ..database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        stmt = select(self.model).filter(self.model.id == id)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.filter(self.model.deleted_at == None)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        stmt = select(self.model).offset(skip).limit(limit)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.filter(self.model.deleted_at == None)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        obj_in_data = obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
        db_obj = self.model(**obj_in_data, **kwargs)  # type: ignore
        db.add(db_obj)
        try:
            await db.commit()
            await db.refresh(db_obj)
        except SQLAlchemyError:
            await db.rollback()
            raise
        return db_obj

    async def update(
        self, db: AsyncSession, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        try:
            await db.commit()
            await db.refresh(db_obj)
        except SQLAlchemyError:
            await db.rollback()
            raise
        return db_obj

    async def remove(self, db: AsyncSession, *, id: int) -> ModelType:
        stmt = select(self.model).filter(self.model.id == id)
        result = await db.execute(stmt)
        obj = result.scalars().first()
        if obj:
            if hasattr(obj, "deleted_at"):
                from datetime import datetime, timezone
                obj.deleted_at = datetime.now(timezone.utc)
            else:
                await db.delete(obj)
            try:
                await db.commit()
            except SQLAlchemyError:
                await db.rollback()
                raise
        return obj

    async def delete(self, db: AsyncSession, *, db_obj: ModelType) -> ModelType:
        if hasattr(db_obj, "deleted_at"):
            from datetime import datetime, timezone
            db_obj.deleted_at = datetime.now(timezone.utc)
        else:
            await db.delete(db_obj)
        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise
        return db_obj
