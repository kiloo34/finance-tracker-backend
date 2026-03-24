"""
Background Jobs — Debt Reminder

Runs once per day to notify users of upcoming or overdue debts.
Extracted from main.py to keep the app factory clean.
"""
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from ..database import AsyncSessionLocal
from ..models import Obligation, ObligationType, Notification, NotificationStatus, DebtStatus


async def debt_reminder_job() -> None:
    """
    Continuously checks for unpaid obligations (payables) due within 3 days or already overdue.
    Creates a daily notification for the owning user if one has not been sent yet today.
    """
    while True:
        try:
            async with AsyncSessionLocal() as db:
                today = datetime.now().date()
                target_date = today + timedelta(days=3)

                # Query unpaid obligations (payables) due on or before target_date
                stmt = select(Obligation).filter(
                    Obligation.type == ObligationType.payable,
                    Obligation.status == DebtStatus.unpaid,
                    Obligation.due_date <= target_date,
                )
                result = await db.execute(stmt)
                due_obligations = result.scalars().all()

                for obl in due_obligations:
                    title = "Debt Reminder"
                    message = (
                        f"Your debt '{obl.contact_name}' for {obl.remaining_amount} "
                        f"is due on {obl.due_date}."
                    )

                    # Prevent duplicate notifications for the same debt on the same day
                    dup_stmt = select(Notification).filter(
                        Notification.user_id == debt.user_id,
                        Notification.title == title,
                        Notification.message == message,
                        Notification.created_at >= datetime.combine(today, datetime.min.time()),
                    )
                    existing = await db.execute(dup_stmt)

                    if not existing.scalars().first():
                        db.add(Notification(
                            user_id=debt.user_id,
                            title=title,
                            message=message,
                            status=NotificationStatus.unread,
                        ))

                await db.commit()

        except asyncio.CancelledError:
            # Raised when the task is cancelled on shutdown — exit cleanly.
            break
        except Exception as exc:
            print(f"[debt_reminder_job] Error: {exc}")

        # Run once a day
        await asyncio.sleep(86_400)
