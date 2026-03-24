from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repo import CRUDBase
from ..models import Obligation
from ..schemas import ObligationCreate

class RepositoryObligation(CRUDBase[Obligation, ObligationCreate, ObligationCreate]):
    async def get_by_user(self, db: AsyncSession, type: str | None = None, skip: int = 0, limit: int = 100) -> List[Obligation]:
        query = select(self.model).filter(self.model.deleted_at == None)
        if type:
            query = query.filter(self.model.type == type)
        
        result = await db.execute(
            query.order_by(self.model.created_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())
        
    async def get_by_id_and_user(self, db: AsyncSession, obligation_id: int, user_id: int) -> Obligation | None:
        result = await db.execute(
            select(self.model).filter(self.model.id == obligation_id, self.model.user_id == user_id, self.model.deleted_at == None)
        )
        return result.scalars().first()

obligation_repo = RepositoryObligation(Obligation)
