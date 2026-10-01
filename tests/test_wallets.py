import asyncio
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_wallet(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/wallets")
    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(data["balance"]) == Decimal("0.00")
    uuid.UUID(data["id"])  # valid uuid


@pytest.mark.asyncio
async def test_get_wallet_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/wallets/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_deposit(client: AsyncClient) -> None:
    wallet_id = (await client.post("/api/v1/wallets")).json()["id"]
    resp = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": "1000.00"},
    )
    assert resp.status_code == 200
    assert Decimal(resp.json()["balance"]) == Decimal("1000.00")


@pytest.mark.asyncio
async def test_withdraw(client: AsyncClient) -> None:
    wallet_id = (await client.post("/api/v1/wallets")).json()["id"]
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": "1000.00"},
    )
    resp = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": "300.50"},
    )
    assert resp.status_code == 200
    assert Decimal(resp.json()["balance"]) == Decimal("699.50")


@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(client: AsyncClient) -> None:
    wallet_id = (await client.post("/api/v1/wallets")).json()["id"]
    resp = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": "100.00"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_operation_invalid_amount(client: AsyncClient) -> None:
    wallet_id = (await client.post("/api/v1/wallets")).json()["id"]
    resp = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": "-100"},
    )
    assert resp.status_code == 422  # validation error


@pytest.mark.asyncio
async def test_operation_invalid_type(client: AsyncClient) -> None:
    wallet_id = (await client.post("/api/v1/wallets")).json()["id"]
    resp = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "TRANSFER", "amount": "100"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_operation_wallet_not_found(client: AsyncClient) -> None:
    resp = await client.post(
        f"/api/v1/wallets/{uuid.uuid4()}/operation",
        json={"operation_type": "DEPOSIT", "amount": "100"},
    )
    assert resp.status_code == 404