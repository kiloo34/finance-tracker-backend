"""
Unit tests for debt CRUD endpoints:
  GET  /debts/
  POST /debts/
  PUT  /debts/{id}
  DELETE /debts/{id}
"""
import pytest
from httpx import AsyncClient

DEBT_PAYLOAD = {
    "creditor_name": "Bank BCA",
    "amount": 10000000.0,
    "remaining_amount": 10000000.0,
    "due_date": "2026-12-31",
    "status": "unpaid",
    "description": "KPR test loan"
}

UPDATE_PAYLOAD = {
    "creditor_name": "Bank BCA",
    "amount": 10000000.0,
    "remaining_amount": 5000000.0,
    "due_date": "2026-12-31",
    "status": "partially_paid",
    "description": "KPR test loan - half paid"
}


class TestDebtCRUD:
    """Core CRUD operations for debts."""

    @pytest.mark.asyncio
    async def test_get_debts_empty(self, client: AsyncClient, auth_headers):
        """Fresh user should have an empty debts list."""
        # Use a fresh user to avoid interference
        await client.post("/auth/register", json={"username": "debt_tester_1", "password": "password123"})
        res_login = await client.post("/auth/login", data={"username": "debt_tester_1", "password": "password123"})
        fresh_headers = {"Authorization": f"Bearer {res_login.json()['access_token']}"}
        
        res = await client.get("/debts/", headers=fresh_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    @pytest.mark.asyncio
    async def test_create_debt(self, client: AsyncClient, auth_headers):
        """POST should create a debt and return schema with id."""
        res = await client.post("/debts/", json=DEBT_PAYLOAD, headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert "id" in body
        assert body["creditor_name"] == "Bank BCA"
        assert body["status"] == "unpaid"

    @pytest.mark.asyncio
    async def test_update_debt(self, client: AsyncClient, auth_headers):
        """PUT should update the debt and return the updated object."""
        create_res = await client.post("/debts/", json=DEBT_PAYLOAD, headers=auth_headers)
        debt_id = create_res.json()["id"]

        update_res = await client.put(f"/debts/{debt_id}", json=UPDATE_PAYLOAD, headers=auth_headers)
        assert update_res.status_code == 200
        body = update_res.json()
        assert body["status"] == "partially_paid"
        assert body["remaining_amount"] == 5000000.0

    @pytest.mark.asyncio
    async def test_delete_debt(self, client: AsyncClient, auth_headers):
        """DELETE should remove the debt."""
        create_res = await client.post("/debts/", json=DEBT_PAYLOAD, headers=auth_headers)
        debt_id = create_res.json()["id"]

        del_res = await client.delete(f"/debts/{debt_id}", headers=auth_headers)
        assert del_res.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_nonexistent_debt(self, client: AsyncClient, auth_headers):
        """Deleting non-existent debt id must return 404."""
        res = await client.delete("/debts/99999", headers=auth_headers)
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_update_nonexistent_debt(self, client: AsyncClient, auth_headers):
        """Updating non-existent debt id must return 404."""
        res = await client.put("/debts/99999", json=UPDATE_PAYLOAD, headers=auth_headers)
        assert res.status_code == 404


class TestDebtUserIsolation:
    """Verify user A cannot access user B's debts."""

    @pytest.mark.asyncio
    async def test_user_cannot_delete_other_users_debt(self, client: AsyncClient, auth_headers):
        """User B should get 404 when trying to delete User A's debt."""
        create_res = await client.post("/debts/", json=DEBT_PAYLOAD, headers=auth_headers)
        debt_id = create_res.json()["id"]

        await client.post("/auth/register", json={"username": "user_b_debt", "password": "password789"})
        login_res = await client.post("/auth/login", data={"username": "user_b_debt", "password": "password789"})
        user_b_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        res = await client.delete(f"/debts/{debt_id}", headers=user_b_headers)
        assert res.status_code == 404
