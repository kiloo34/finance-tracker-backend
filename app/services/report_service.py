from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, extract
from ..models import Transaction, Category, TransactionType

class ReportService:
    async def get_summary(
        self,
        db: AsyncSession,
        user_id: int,
        month: int | None = None,
        year: int | None = None
    ):
        """
        Calculates total income, expenses, and groups transactions by category
        for a specific period or all time.
        """
        # Base queries
        tx_stmt = select(Transaction).filter(Transaction.user_id == user_id)
        
        if month:
            tx_stmt = tx_stmt.filter(extract('month', Transaction.transaction_date) == month)
        if year:
            tx_stmt = tx_stmt.filter(extract('year', Transaction.transaction_date) == year)

        # 1. Get raw totals
        tx_result = await db.execute(tx_stmt)
        transactions = tx_result.scalars().all()

        total_income = sum(t.amount for t in transactions if t.type == TransactionType.income)
        total_expense = sum(t.amount for t in transactions if t.type == TransactionType.expense)
        net_savings = total_income - total_expense
        expense_ratio = (total_expense / total_income * 100) if total_income > 0 else 0.0

        # 2. Group by category
        # Using a dictionary to aggregate amounts per category_id
        category_totals = {}
        for t in transactions:
            cat_id = t.category_id or 0 # 0 for Uncategorized
            if cat_id not in category_totals:
                category_totals[cat_id] = {
                    "category_id": t.category_id,
                    "total_amount": 0.0,
                    "type": t.type.value
                }
            category_totals[cat_id]["total_amount"] += t.amount

        # 3. Resolve category names
        categories_response = []
        if category_totals:
            # Fetch all user categories to map IDs to names
            cat_stmt = select(Category).filter(Category.user_id == user_id)
            cat_res = await db.execute(cat_stmt)
            cats = {c.id: c.name for c in cat_res.scalars().all()}
            
            for cat_id, data in category_totals.items():
                cat_name = cats.get(cat_id, "Uncategorized")
                categories_response.append({
                    "category_id": data["category_id"],
                    "category_name": cat_name,
                    "total_amount": data["total_amount"],
                    "type": data["type"]
                })
                
        # Sort by highest amount
        categories_response.sort(key=lambda x: x["total_amount"], reverse=True)

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "expense_ratio": round(expense_ratio, 2),
            "categories": categories_response
        }

report_service = ReportService()
