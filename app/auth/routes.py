from fastapi import APIRouter, Depends, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas, database, models
from ..services.auth_service import auth_service
from . import jwt
from ..core.limiter import limiter

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register", response_model=schemas.UserResponse)
@limiter.limit("10/minute")
async def register_user(
    request: Request,
    user: schemas.UserCreate,
    db: AsyncSession = Depends(database.get_db)
):
    """Register a new user. Rate limited to 10 per minute per IP."""
    return await auth_service.register(db=db, user_data=user)


@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(database.get_db)
):
    """
    Authenticate and receive a JWT.
    Rate limited to 5 attempts per minute per IP (brute-force protection).
    Creates a tracked session record on success.
    """
    # Explicitly extract remember_me from the form body.
    # FastAPI's OAuth2PasswordRequestForm sometimes consumes the body if not handled carefully.
    form_payload = await request.form()
    remember_me_val = form_payload.get("remember_me", "false").lower()
    remember_me = remember_me_val == "true"

    return await auth_service.attempt_login(
        db=db,
        username=form_data.username,
        password=form_data.password,
        request=request,
        remember_me=remember_me,
    )


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user),
    token: str = Depends(jwt.oauth2_scheme),
):
    """Revoke the current session (logout this device only)."""
    session_id = await jwt.get_session_id_from_token(token=token)
    if not session_id:
        return {"message": "Logged out (no session to revoke)."}
    return await auth_service.logout(db=db, session_id=session_id, user_id=current_user.id)


@router.post("/logout-all")
async def logout_all_devices(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user),
    token: str = Depends(jwt.oauth2_scheme),
):
    """Revoke ALL other sessions — logs the user out from every other device."""
    session_id = await jwt.get_session_id_from_token(token=token)
    return await auth_service.logout_all(
        db=db,
        user_id=current_user.id,
        current_session_id=session_id or "",
    )


@router.post("/upgrade")
async def upgrade_tier(
    db: AsyncSession = Depends(database.get_db),
    current_user: models.User = Depends(jwt.get_current_user)
):
    """Upgrade the current user's tier to Premium."""
    return await auth_service.upgrade_tier(db=db, username=current_user.username)
