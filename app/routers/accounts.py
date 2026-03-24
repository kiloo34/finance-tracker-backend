from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from decimal import Decimal
from datetime import date
from ..database import get_db
from .. import models, schemas, auth

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=schemas.AccountResponse)
async def create_account(
    account: schemas.AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    db_account = models.Account(
        user_id=current_user.id,
        account_number=account.account_number,
        owner_name=account.owner_name,
    )
    db.add(db_account)
    await db.commit()
    await db.refresh(db_account)
    return db_account


@router.get("/", response_model=List[schemas.AccountResponse])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = await db.execute(
        select(models.Account)
        .where(models.Account.user_id == current_user.id)
        .order_by(models.Account.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{account_id}/pockets", response_model=schemas.PocketResponse)
async def create_pocket(
    account_id: int,
    pocket: schemas.PocketBase,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # Verify account ownership
    result = await db.execute(
        select(models.Account).where(
            models.Account.id == account_id,
            models.Account.user_id == current_user.id,
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    db_pocket = models.Pocket(
        account_id=account_id,
        pocket_number=pocket.pocket_number,
        name=pocket.name,
        sort=pocket.sort,
        currency=pocket.currency,
    )
    db.add(db_pocket)
    await db.commit()
    await db.refresh(db_pocket)
    return db_pocket


@router.get("/{account_id}/pockets", response_model=List[schemas.PocketResponse])
async def list_pockets(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    result = await db.execute(
        select(models.Account).where(
            models.Account.id == account_id,
            models.Account.user_id == current_user.id,
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    pockets_result = await db.execute(
        select(models.Pocket).where(models.Pocket.account_id == account_id)
    )
    return pockets_result.scalars().all()


@router.post("/transfer")
async def transfer_funds(
    source_pocket_id: int,
    destination_pocket_id: int,
    amount: Decimal,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # Load source pocket (must belong to current user's account)
    source_result = await db.execute(
        select(models.Pocket)
        .join(models.Account)
        .where(
            models.Pocket.id == source_pocket_id,
            models.Account.user_id == current_user.id,
        )
    )
    source = source_result.scalars().first()

    dest_result = await db.execute(
        select(models.Pocket)
        .join(models.Account)
        .where(
            models.Pocket.id == destination_pocket_id,
            models.Account.user_id == current_user.id,
        )
    )
    dest = dest_result.scalars().first()

    if not source or not dest:
        raise HTTPException(status_code=404, detail="One or both pockets not found")

    # Business Rule: intra-account transfers only
    if source.account_id != dest.account_id:
        raise HTTPException(
            status_code=400,
            detail="Transfers only allowed between pockets of the same account",
        )

    if source.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds in source pocket")

    # Perform transfer
    source.balance -= amount
    dest.balance += amount

    # Audit transaction record
    tx = models.Transaction(
        user_id=current_user.id,
        actor_id=current_user.id,
        source_pocket_id=source_pocket_id,
        destination_pocket_id=destination_pocket_id,
        amount=amount,
        action=models.TxAction.transfer,
        description=f"Internal transfer from {source.name} to {dest.name}",
        transaction_date=date.today(),
    )
    db.add(tx)
    await db.commit()

    return {
        "message": "Transfer successful",
        "source_balance": float(source.balance),
        "dest_balance": float(dest.balance),
    }
