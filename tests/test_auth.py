"""
Unit tests for authentication endpoints:
  POST /auth/register
  POST /auth/login
  Protected route access validation
"""
import pytest
from httpx import AsyncClient


# ── Registration ─────────────────────────────────────────────────────────────

class TestRegister:
    """Tests for the /auth/register endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """New unique username should register and return user schema."""
        res = await client.post("/auth/register", json={
            "username": "newuser_register",
            "password": "securepassword123"
        })
        assert res.status_code == 200
        body = res.json()
        assert "id" in body
        assert body["username"] == "newuser_register"
        assert "hashed_password" not in body    # password must never leak

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient):
        """Registering an already-registered username must return 400."""
        payload = {"username": "dup_user", "password": "password123"}
        await client.post("/auth/register", json=payload)
        res = await client.post("/auth/register", json=payload)
        assert res.status_code == 400
        assert "already registered" in res.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_short_password_fails_validation(self, client: AsyncClient):
        """Password shorter than 6 chars must be rejected with 422 (Pydantic validation)."""
        res = await client.post("/auth/register", json={
            "username": "badpwduser",
            "password": "12"
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_username_fails_validation(self, client: AsyncClient):
        """Username shorter than 3 chars must be rejected with 422."""
        res = await client.post("/auth/register", json={
            "username": "ab",
            "password": "validpassword"
        })
        assert res.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_username_characters(self, client: AsyncClient):
        """Username with spaces or special chars must be rejected (pattern constraint)."""
        res = await client.post("/auth/register", json={
            "username": "invalid user!",
            "password": "validpassword"
        })
        assert res.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    """Tests for the /auth/login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, registered_user):
        """Valid credentials must return a Bearer access_token."""
        res = await client.post("/auth/login", data={
            "username": registered_user["username"],
            "password": registered_user["password"]
        })
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert "role" in body
        assert "tier" in body

    @pytest.mark.asyncio
    async def test_login_remember_me(self, client: AsyncClient, registered_user):
        """Login with remember_me=true should succeed."""
        res = await client.post("/auth/login", data={
            "username": registered_user["username"],
            "password": registered_user["password"],
            "remember_me": "true"
        })
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, registered_user):
        """Wrong password must return 401 Unauthorized."""
        res = await client.post("/auth/login", data={
            "username": registered_user["username"],
            "password": "wrongpassword"
        })
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Login with unknown username must return 401."""
        res = await client.post("/auth/login", data={
            "username": "ghost_user_xyz",
            "password": "somepassword"
        })
        assert res.status_code == 401
    
    @pytest.mark.asyncio
    async def test_login_rate_limiting(self, client: AsyncClient):
        """Hitting the login endpoint more than 5 times per minute should return 429."""
        # The limit is 5/minute, so making 6 requests should trigger the rate limit.
        for _ in range(5):
            res = await client.post("/auth/login", data={"username": "test_user", "password": "wrong"})
            assert res.status_code in [401, 200]  # Valid or invalid, but not rate-limited yet
            
        res = await client.post("/auth/login", data={"username": "test_user", "password": "wrong"})
        assert res.status_code == 429
        
    @pytest.mark.asyncio
    async def test_register_rate_limiting(self, client: AsyncClient):
        """Hitting the register endpoint more than 10 times per minute should return 429."""
        # The limit is 10/minute
        for i in range(10):
            res = await client.post("/auth/register", json={"username": f"user_{i}", "password": "password123"})
            assert res.status_code in [200, 422, 400]
            
        res = await client.post("/auth/register", json={"username": "user_11", "password": "password123"})
        assert res.status_code == 429


# ── JWT Protection ─────────────────────────────────────────────────────────────

class TestJWTProtection:
    """Tests verifying that protected routes enforce JWT authentication."""

    @pytest.mark.asyncio
    async def test_protected_route_without_token(self, client: AsyncClient):
        """Requests without Authorization header must return 401."""
        res = await client.get("/transactions/")
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_route_with_invalid_token(self, client: AsyncClient):
        """Requests with a malformed JWT must return 401."""
        res = await client.get("/transactions/", headers={"Authorization": "Bearer INVALID.TOKEN.HERE"})
        assert res.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_route_with_valid_token(self, client: AsyncClient, auth_headers):
        """Requests with a valid JWT must be accepted by the server."""
        res = await client.get("/transactions/", headers=auth_headers)
        assert res.status_code == 200
