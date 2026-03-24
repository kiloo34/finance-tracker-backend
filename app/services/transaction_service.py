from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from decimal import Decimal
from ..schemas import TransactionCreate
from .. import models
from ..repositories.transaction_repo import transaction_repo


class TransactionService:
    async def get_user_transactions(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100):
        return await transaction_repo.get_by_user(db, user_id=user_id, skip=skip, limit=limit)

    async def create_transaction(self, db: AsyncSession, transaction_in: TransactionCreate, user_id: int):
        # 1. Validate Category hierarchy if parent_id is used (optional check)
        
        # 2. Business Rules for Pockets
        if transaction_in.source_pocket_id:
            from sqlalchemy import select
            res = await db.execute(select(models.Pocket).filter(models.Pocket.id == transaction_in.source_pocket_id))
            source = res.scalar_one_or_none()
            if not source:
                raise HTTPException(status_code=404, detail="Source pocket not found")
            
            # Rule: Saving pockets cannot spend directly
            if source.sort == models.PocketSort.saving and transaction_in.action == models.TxAction.expense:
                raise HTTPException(status_code=400, detail="Cannot spend directly from a Saving pocket. Move funds to a Spending pocket first.")
            
            # Adjust balance
            source.balance -= Decimal(str(transaction_in.amount))

        if transaction_in.destination_pocket_id:
            from sqlalchemy import select
            res = await db.execute(select(models.Pocket).filter(models.Pocket.id == transaction_in.destination_pocket_id))
            dest = res.scalar_one_or_none()
            if not dest:
                raise HTTPException(status_code=404, detail="Destination pocket not found")
            
            # Adjust balance
            dest.balance += Decimal(str(transaction_in.amount))

        return await transaction_repo.create(db, obj_in=transaction_in, user_id=user_id)

    async def update_transaction(self, db: AsyncSession, transaction_id: int, transaction_in: TransactionCreate, user_id: int):
        # Note: In a real system, updating a transaction involves reversing old balance changes and applying new ones.
        # This is a complex operation typically handled with double-entry bookkeeping.
        db_txn = await transaction_repo.get_by_id_and_user(db, transaction_id=transaction_id, user_id=user_id)
        if not db_txn:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return await transaction_repo.update(db, db_obj=db_txn, obj_in=transaction_in)

    async def delete_transaction(self, db: AsyncSession, transaction_id: int, user_id: int):
        db_txn = await transaction_repo.get_by_id_and_user(db, transaction_id=transaction_id, user_id=user_id)
        if not db_txn:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return await transaction_repo.delete(db, db_obj=db_txn)


transaction_service = TransactionService()
