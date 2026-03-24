from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repo import CRUDBase
from ..models import Transaction
from ..schemas import TransactionCreate

class RepositoryTransaction(CRUDBase[Transaction, TransactionCreate, TransactionCreate]):
    async def get_by_user(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> List[Transaction]:
        stmt = select(self.model).filter(self.model.user_id == user_id, self.model.deleted_at == None).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return list(result.scalars().all())
        
    async def get_by_id_and_user(self, db: AsyncSession, transaction_id: int, user_id: int) -> Transaction | None:
        stmt = select(self.model).filter(self.model.id == transaction_id, self.model.user_id == user_id, self.model.deleted_at == None)
        result = await db.execute(stmt)
        return result.scalars().first()

transaction_repo = RepositoryTransaction(Transaction)
