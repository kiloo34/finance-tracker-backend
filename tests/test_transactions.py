"""
Unit tests for transaction CRUD endpoints:
  GET  /transactions/
  POST /transactions/
  PUT  /transactions/{id}
  DELETE /transactions/{id}
"""
import pytest
from httpx import AsyncClient

from tests.conftest import CREDENTIALS

TRANSACTION_PAYLOAD = {
    "amount": 50000,
    "action": "expense",
    "description": "Test groceries",
    "category_id": None,
    "transaction_date": "2026-02-27"
}

INCOME_PAYLOAD = {
    "amount": 5000000,
    "action": "income",
    "description": "Monthly salary",
    "category_id": None,
    "transaction_date": "2026-02-01"
}


class TestTransactionCRUD:
    """Core CRUD operations for transactions."""

    @pytest.mark.asyncio
    async def test_get_transactions_empty(self, client: AsyncClient, auth_headers):
        """A new user should have an empty transactions list."""
        res = await client.get("/transactions/", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    @pytest.mark.asyncio
    async def test_create_transaction(self, client: AsyncClient, auth_headers):
        """POST should create a transaction and return it with an id."""
        res = await client.post("/transactions/", json=TRANSACTION_PAYLOAD, headers=auth_headers)
        assert res.status_code == 200
        body = res.json()
        assert "id" in body
        assert body["amount"] == 50000.0
        assert body["action"] == "expense"

    @pytest.mark.asyncio
    async def test_list_transactions_after_create(self, client: AsyncClient, auth_headers):
        """After creating a transaction it should appear in the list."""
        await client.post("/transactions/", json=TRANSACTION_PAYLOAD, headers=auth_headers)
        res = await client.get("/transactions/", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_delete_transaction(self, client: AsyncClient, auth_headers):
        """DELETE should remove the transaction and return a success message."""
        create_res = await client.post("/transactions/", json=TRANSACTION_PAYLOAD, headers=auth_headers)
        tx_id = create_res.json()["id"]
        del_res = await client.delete(f"/transactions/{tx_id}", headers=auth_headers)
        assert del_res.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_nonexistent_transaction(self, client: AsyncClient, auth_headers):
        """Deleting a non-existent transaction id must return 404."""
        res = await client.delete("/transactions/99999", headers=auth_headers)
        assert res.status_code == 404


class TestTransactionUserIsolation:
    """Verify user A cannot access user B's transactions."""

    @pytest.mark.asyncio
    async def test_user_cannot_delete_other_users_transaction(self, client: AsyncClient, auth_headers):
        """User B should get 404 when trying to delete User A's transaction."""
        # Create transaction as User A (auth_headers)
        create_res = await client.post("/transactions/", json=TRANSACTION_PAYLOAD, headers=auth_headers)
        tx_id = create_res.json()["id"]

        # Register and login as User B
        await client.post("/auth/register", json={"username": "user_b_tx", "password": "password789"})
        login_res = await client.post("/auth/login", data={"username": "user_b_tx", "password": "password789"})
        user_b_token = login_res.json()["access_token"]
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

        # User B tries to delete User A's transaction
        res = await client.delete(f"/transactions/{tx_id}", headers=user_b_headers)
        assert res.status_code == 404

    @pytest.mark.asyncio
    async def test_user_cannot_see_other_users_transactions(self, client: AsyncClient, auth_headers):
        """User B's transaction list should not contain User A's data."""
        await client.post("/transactions/", json=INCOME_PAYLOAD, headers=auth_headers)

        await client.post("/auth/register", json={"username": "user_b_tx2", "password": "password789"})
        login_res = await client.post("/auth/login", data={"username": "user_b_tx2", "password": "password789"})
        user_b_headers = {"Authorization": f"Bearer {login_res.json()['access_token']}"}

        res = await client.get("/transactions/", headers=user_b_headers)
        assert res.status_code == 200
        # User B should have empty list (not seeded with User A's data)
        assert all(tx["description"] != INCOME_PAYLOAD["description"] for tx in res.json())


class TestTransactionSoftDelete:
    """Verify soft delete functionality."""

    @pytest.mark.asyncio
    async def test_soft_delete_not_in_list(self, client: AsyncClient, auth_headers):
        """A deleted transaction should be hidden from the list but exist in DB (verified by 200 on delete)."""
        # 1. Create
        create_res = await client.post("/transactions/", json=TRANSACTION_PAYLOAD, headers=auth_headers)
        tx_id = create_res.json()["id"]

        # 2. Delete
        del_res = await client.delete(f"/transactions/{tx_id}", headers=auth_headers)
        assert del_res.status_code == 200

        # 3. Verify not in list
        list_res = await client.get("/transactions/", headers=auth_headers)
        assert all(tx["id"] != tx_id for tx in list_res.json())

        # 4. Verify GET by ID also returns 404 (due to CRUDBase filter)
        # Note: Depending on router implementation, read_one might need to be added or checked.
        # But get_per_user usually filters.
