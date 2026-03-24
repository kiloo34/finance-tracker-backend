from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Request, status
from datetime import timedelta
import json
from user_agents import parse as parse_ua
from .. import schemas, models
from ..repositories.user_repo import user_repo
from ..repositories.session_repo import session_repo
from ..core import security
from ..auth import jwt


def _parse_device_hint(user_agent_str: str | None) -> str:
    """Convert a raw User-Agent string into a human-readable device description."""
    if not user_agent_str:
        return "Unknown Device"
    ua = parse_ua(user_agent_str)
    browser = ua.browser.family or "Unknown Browser"
    os_name = ua.os.family or "Unknown OS"
    if ua.is_mobile:
        return f"📱 {ua.device.family} ({browser})"
    if ua.is_tablet:
        return f"📱 Tablet — {os_name} ({browser})"
    return f"💻 {os_name} — {browser}"


class AuthService:
    async def register(self, db: AsyncSession, user_data: schemas.UserCreate) -> schemas.UserResponse:
        db_user = await user_repo.get_by_username(db, username=user_data.username)
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        return await user_repo.create_user(db=db, obj_in=user_data)

    async def attempt_login(
        self,
        db: AsyncSession,
        username: str,
        password: str,
        request: Request,
        remember_me: bool = False,
    ) -> dict:
        """
        Authenticate user, create a tracked session, and return a JWT
        with the session ID embedded as the jti claim.
        """
        # User can login with username, email, or phone_number
        user = await user_repo.get_by_login_identifier(db, identifier=username)
        if not user or not security.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate unique session ID to use as JWT jti
        session_id = jwt.generate_session_id()

        # Capture request context for session tracking
        ip_address = request.client.host if request.client else "unknown"
        user_agent_str = request.headers.get("user-agent", "")
        device_hint = _parse_device_hint(user_agent_str)

        # Persist session row BEFORE issuing the token
        await session_repo.create(
            db=db,
            session_id=session_id,
            user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent_str[:512],
            device_hint=device_hint,
        )

        # 1 day by default, 30 days if remember_me is checked
        duration = timedelta(days=30) if remember_me else timedelta(days=1)
        access_token = jwt.create_access_token(
            data={
                "sub": user.username,
                "role": user.role,
                "tier": user.tier,
                "user_id": user.id,
                "jti": session_id,          # Embed session ID as JWT identity claim
            },
            expires_delta=duration
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": user.role,
            "tier": user.tier,
            "session_id": session_id,
        }

    async def logout(self, db: AsyncSession, session_id: str, user_id: int) -> dict:
        """Revoke the current session (logout this device only)."""
        await session_repo.revoke(db=db, session_id=session_id, user_id=user_id)
        return {"message": "Logged out successfully."}

    async def logout_all(self, db: AsyncSession, user_id: int, current_session_id: str) -> dict:
        """Revoke ALL other sessions (logout from every device except the current one)."""
        count = await session_repo.revoke_all(db=db, user_id=user_id, except_session_id=current_session_id)
        return {"message": f"Logged out from {count} other device(s)."}

    async def upgrade_tier(self, db: AsyncSession, username: str) -> dict:
        user = await user_repo.get_by_username(db, username=username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.tier = models.UserTier.premium
        await db.commit()
        await db.refresh(user)
        return {"message": "Successfully upgraded to Premium!", "tier": user.tier}


# Singleton instance for dependency injection
auth_service = AuthService()
