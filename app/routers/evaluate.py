from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from .. import database, models, schemas
from ..auth.jwt import get_current_user
from ..services.evaluate_service import evaluate_service

router = APIRouter(
    prefix="/evaluate",
    tags=["Evaluation"]
)

@router.get("/", response_model=schemas.FinancialEvaluationResponse)
async def evaluate_finances(
    background_tasks: BackgroundTasks,
    month: int | None = None,
    year: int | None = None,
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Returns the financial evaluation for the current user.
    If the expense ratio is > 80% ("Boros"), a warning notification is written
    in the background after this response is returned.
    """
    return await evaluate_service.evaluate_finances(
        db=db,
        user_id=current_user.id,
        background_tasks=background_tasks,
        month=month,
        year=year
    )
