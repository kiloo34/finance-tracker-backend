from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..schemas import ObligationCreate, TransactionCreate, CategoryCreate
from ..repositories.obligation_repo import obligation_repo
from ..models import TransactionType, ObligationType
from .transaction_service import transaction_service
from .category_service import category_service
from datetime import date

class ObligationService:
    async def get_user_obligations(self, db: AsyncSession, user_id: int, type: ObligationType | None = None, skip: int = 0, limit: int = 100):
        return await obligation_repo.get_by_user(db, user_id=user_id, type=type, skip=skip, limit=limit)

    async def create_obligation(self, db: AsyncSession, obj_in: ObligationCreate, user_id: int):
        return await obligation_repo.create(db, obj_in=obj_in, user_id=user_id)

    async def update_obligation(self, db: AsyncSession, obligation_id: int, obj_in: ObligationCreate, user_id: int):
        db_obj = await obligation_repo.get_by_id_and_user(db, obligation_id=obligation_id, user_id=user_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Obligation not found")

        # Calculate payment delta for COA automation
        old_rem = float(db_obj.remaining_amount)
        new_rem = float(obj_in.remaining_amount)
        payment_amount = old_rem - new_rem

        if payment_amount > 0:
            # Determine category and transaction type
            is_receivable = db_obj.type == ObligationType.receivable
            cat_name = "Receivable Collection" if is_receivable else "Debt Payment"
            txn_type = TransactionType.income if is_receivable else TransactionType.expense
            
            # Ensure category exists
            categories = await category_service.get_user_categories(db, user_id=user_id)
            category = next((c for c in categories if c.name == cat_name and c.type == txn_type), None)
            
            if not category:
                category = await category_service.create_category(
                    db, 
                    CategoryCreate(name=cat_name, type=txn_type, description=f"Automated category for {db_obj.type} payments"),
                    user_id=user_id
                )
            
            # Record linked transaction
            await transaction_service.create_transaction(
                db,
                TransactionCreate(
                    amount=payment_amount,
                    action=txn_type,
                    category_id=category.id,
                    description=f"{db_obj.type.capitalize()} payment: {db_obj.contact_name}",
                    transaction_date=date.today(),
                    resource_type="Obligation",
                    resource_id=db_obj.id
                ),
                user_id=user_id
            )

        return await obligation_repo.update(db, db_obj=db_obj, obj_in=obj_in)

    async def delete_obligation(self, db: AsyncSession, obligation_id: int, user_id: int):
        db_obj = await obligation_repo.get_by_id_and_user(db, obligation_id=obligation_id, user_id=user_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Obligation not found")
        await obligation_repo.remove(db, id=db_obj.id)
        return {"message": "Obligation deleted successfully"}

obligation_service = ObligationService()
