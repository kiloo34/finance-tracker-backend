from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from .. import schemas, database, models
from ..auth.jwt import get_current_user, get_session_id_from_token, oauth2_scheme
from ..services.transaction_service import transaction_service
from ..core.audit import log_action

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.TransactionResponse])
async def read_transactions(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    request: Request = None,
):
    return await transaction_service.get_user_transactions(db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/export/csv")
async def export_transactions_csv(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    from fastapi.responses import StreamingResponse
    import io
    import csv

    # Fetch all user transactions
    transactions = await transaction_service.get_user_transactions(db, user_id=current_user.id, skip=0, limit=100000)
    
    # Create the CSV in memory
    stream = io.StringIO()
    writer = csv.writer(stream)
    
    # Header
    writer.writerow(["ID", "Date", "Type", "Amount", "Description", "Category ID", "Created At"])
    
    for t in transactions:
        writer.writerow([
            t.id,
            t.transaction_date.isoformat(),
            t.action.value,
            t.amount,
            t.description or "",
            t.category_id or "",
            t.created_at.isoformat()
        ])
        
    stream.seek(0)
    
    response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=transactions_{current_user.username}.csv"
    return response


@router.post("/", response_model=schemas.TransactionResponse)
async def create_transaction(
    transaction: schemas.TransactionCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    result = await transaction_service.create_transaction(db=db, transaction_in=transaction, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="transaction.create",
        session_id=session_id, resource_type="Transaction", resource_id=result.id,
        ip_address=request.client.host if request.client else None,
        detail={"amount": transaction.amount, "action": transaction.action, "description": transaction.description},
    )
    return result


@router.put("/{transaction_id}", response_model=schemas.TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction: schemas.TransactionCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    result = await transaction_service.update_transaction(db, transaction_id=transaction_id, transaction_in=transaction, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="transaction.update",
        session_id=session_id, resource_type="Transaction", resource_id=transaction_id,
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    result = await transaction_service.delete_transaction(db, transaction_id=transaction_id, user_id=current_user.id)
    session_id = await get_session_id_from_token(token=token)
    background_tasks.add_task(
        log_action, db,
        user_id=current_user.id, action="transaction.delete",
        session_id=session_id, resource_type="Transaction", resource_id=transaction_id,
        ip_address=request.client.host if request.client else None,
    )
    return result
