from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .. import models, schemas, database
from ..core.config import settings
from ..models import UserSession, SessionStatus

# JWT Config via Settings
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT with an embedded jti (session ID) claim."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_session_id() -> str:
    """Generate a unique session identifier suitable for use as a JWT jti."""
    return str(uuid.uuid4()).replace("-", "")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(database.get_db)
) -> models.User:
    """
    Validate JWT and verify the embedded session (jti) is still ACTIVE.

    This two-step check means:
    1. JWT cryptographic signature must be valid and not expired.
    2. The session record in DB must exist and NOT be revoked.

    This allows immediate revocation of access even before the JWT expires.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    session_revoked_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session has been revoked. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        jti: str = payload.get("jti")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # Verify the session is still active in the DB
    if jti:
        result = await db.execute(
            select(UserSession).filter(UserSession.id == jti)
        )
        session = result.scalars().first()
        if session is None or session.status != SessionStatus.active:
            raise session_revoked_exception

        # Update last_seen_at asynchronously (fire and forget)
        await db.execute(
            update(UserSession)
            .where(UserSession.id == jti)
            .values(last_seen_at=datetime.now(timezone.utc))
        )
        await db.commit()

    result = await db.execute(
        select(models.User).filter(models.User.username == token_data.username)
    )
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user


async def get_session_id_from_token(token: str = Depends(oauth2_scheme)) -> str | None:
    """Extract the jti (session ID) from the JWT without DB validation (for logout etc.)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("jti")
    except JWTError:
        return None


async def require_admin(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    """
    Dependency that restricts an endpoint to admin users only.

    Usage:
        @router.get("/admin/users")
        async def list_users(admin: models.User = Depends(require_admin)):
            ...

    Raises:
        HTTP 403 Forbidden — if the authenticated user's role is not 'admin'
    """
    if current_user.role != models.UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user
