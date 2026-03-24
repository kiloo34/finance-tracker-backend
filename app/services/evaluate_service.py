from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import BackgroundTasks
from ..models import Transaction, TransactionType, Notification, NotificationStatus


async def _write_boros_notification(user_id: int, ratio: float) -> None:
    """
    Background Task: Silently writes a "Boros" warning notification to the database
    using a fresh session.
    """
    from ..database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        notif = Notification(
            user_id=user_id,
            title="Peringatan Keuangan: Boros",
            message=f"Pengeluaranmu mencapai {round(ratio, 1)}% dari pendapatan! Kurangi pengeluaran yang tidak penting.",
            status=NotificationStatus.unread
        )
        db.add(notif)
        await db.commit()


class EvaluateService:
    async def evaluate_finances(
        self,
        db: AsyncSession,
        user_id: int,
        background_tasks: BackgroundTasks,
        month: int | None = None,
        year: int | None = None
    ):
        # Base query for the user
        stmt = select(Transaction).filter(Transaction.user_id == user_id)
        
        # Apply date filters if provided
        if month_param := month:
            # Using extract from sqlalchemy
            from sqlalchemy import extract
            stmt = stmt.filter(extract('month', Transaction.transaction_date) == month_param)
        if year_param := year:
            from sqlalchemy import extract
            stmt = stmt.filter(extract('year', Transaction.transaction_date) == year_param)

        # Fetch transactions non-blockingly
        result = await db.execute(stmt)
        transactions = result.scalars().all()

        total_income = sum(t.amount for t in transactions if t.type == TransactionType.income)
        total_expense = sum(t.amount for t in transactions if t.type == TransactionType.expense)
        saving = total_income - total_expense

        ratio = 0.0
        if total_income == 0:
            status = "Tidak ada pemasukan"
        else:
            ratio = (total_expense / total_income) * 100
            if ratio < 50:
                status = "Hemat"
            elif ratio <= 80:
                status = "Normal"
            else:
                status = "Boros"
                # Defer notification write to a BackgroundTask — client gets
                # the evaluation result immediately without waiting for DB write.
                background_tasks.add_task(_write_boros_notification, user_id, ratio)

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "saving": saving,
            "expense_ratio_percentage": round(ratio, 2),
            "status": status
        }


evaluate_service = EvaluateService()
