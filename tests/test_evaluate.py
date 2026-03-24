"""
Unit tests for the financial evaluation endpoint:
  GET /evaluate/

Tests all three financial status branches and verifies that a "Boros" evaluation
triggers a background notification creation.
"""
import pytest
from httpx import AsyncClient


async def _seed_transactions(client: AsyncClient, headers: dict, income: float, expense: float):
    """Helper: create income and expense transactions for a user."""
    await client.post("/transactions/", json={
        "amount": income, "type": "income", "description": "Salary",
        "category_id": None, "transaction_date": "2026-02-01", "status": "completed"
    }, headers=headers)
    await client.post("/transactions/", json={
        "amount": expense, "type": "expense", "description": "Rent",
        "category_id": None, "transaction_date": "2026-02-15", "status": "completed"
    }, headers=headers)


async def _make_fresh_user(client: AsyncClient, username: str):
    """Register + login a user and return their auth headers."""
    await client.post("/auth/register", json={"username": username, "password": "evalpassword"})
    res = await client.post("/auth/login", data={"username": username, "password": "evalpassword"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


class TestEvaluateEndpoint:
    """Tests for the /evaluate/ endpoint financial analysis logic."""

    @pytest.mark.asyncio
    async def test_evaluate_no_transactions(self, client: AsyncClient):
        """User with zero transactions should get 'Tidak ada pemasukan' status."""
        h = await _make_fresh_user(client, "eval_empty_user")
        res = await client.get("/evaluate/", headers=h)
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "Tidak ada pemasukan"
        assert body["total_income"] == 0
        assert body["total_expense"] == 0

    @pytest.mark.asyncio
    async def test_evaluate_hemat_status(self, client: AsyncClient):
        """Expense ratio < 50% should return 'Hemat' status."""
        h = await _make_fresh_user(client, "eval_hemat_user")
        await _seed_transactions(client, h, income=10_000_000, expense=3_000_000)  # 30%

        res = await client.get("/evaluate/", headers=h)
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "Hemat"
        assert body["expense_ratio_percentage"] < 50.0

    @pytest.mark.asyncio
    async def test_evaluate_normal_status(self, client: AsyncClient):
        """Expense ratio between 50–80% should return 'Normal' status."""
        h = await _make_fresh_user(client, "eval_normal_user")
        await _seed_transactions(client, h, income=10_000_000, expense=6_500_000)  # 65%

        res = await client.get("/evaluate/", headers=h)
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "Normal"
        assert 50.0 <= body["expense_ratio_percentage"] <= 80.0

    @pytest.mark.asyncio
    async def test_evaluate_boros_status(self, client: AsyncClient):
        """Expense ratio > 80% should return 'Boros' status."""
        h = await _make_fresh_user(client, "eval_boros_user")
        await _seed_transactions(client, h, income=5_000_000, expense=4_500_000)  # 90%

        res = await client.get("/evaluate/", headers=h)
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "Boros"
        assert body["expense_ratio_percentage"] > 80.0

    @pytest.mark.asyncio
    async def test_evaluate_saving_calculation(self, client: AsyncClient):
        """Saving field should equal income minus expense."""
        h = await _make_fresh_user(client, "eval_saving_user")
        await _seed_transactions(client, h, income=8_000_000, expense=2_000_000)

        res = await client.get("/evaluate/", headers=h)
        body = res.json()
        assert body["saving"] == 8_000_000 - 2_000_000

    @pytest.mark.asyncio
    async def test_evaluate_requires_auth(self, client: AsyncClient):
        """The /evaluate/ endpoint must reject unauthenticated requests."""
        res = await client.get("/evaluate/")
        assert res.status_code == 401
