from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas, database, models
from ..auth.jwt import get_current_user
from ..services.report_service import report_service

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/summary", response_model=schemas.ReportSummaryResponse)
async def get_report_summary(
    month: int | None = Query(None, ge=1, le=12, description="Optional month filter (1-12)"),
    year: int | None = Query(None, ge=2000, description="Optional year filter"),
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve summarized financial reporting data (totals and category groupings).
    """
    return await report_service.get_summary(
        db=db,
        user_id=current_user.id,
        month=month,
        year=year
    )
