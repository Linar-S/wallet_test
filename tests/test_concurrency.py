import asyncio
import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_parallel_deposits(client: AsyncClient) -> None:
    """20 параллельных пополнений по 10 - баланс = 200, без потерянных обновлений"""
    wallet_id = (await client.post("/api/v1/wallets")).json()["id"]

    async def deposit() -> None:
        await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": "10.00"},
        )

    await asyncio.gather(*(deposit() for _ in range(20)))

    resp = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert Decimal(resp.json()["balance"]) == Decimal("200.00")


@pytest.mark.asyncio
async def test_parallel_withdraws_never_negative(client: AsyncClient) -> None:
    """Кошелёк с 100: 20 параллельных списаний по 10

    Ровно 10 должны пройти успешно, остальные — получить 409,
    а баланс в итоге должен быть ровно 0 (не отрицательным).
    """
    wallet_id = (await client.post("/api/v1/wallets")).json()["id"]
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": "100.00"},
    )

    async def withdraw() -> int:
        resp = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": "10.00"},
        )
        return resp.status_code

    results = await asyncio.gather(*(withdraw() for _ in range(20)))
    successes = sum(1 for code in results if code == 200)
    conflicts = sum(1 for code in results if code == 409)

    assert successes == 10
    assert conflicts == 10

    final = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert Decimal(final.json()["balance"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_parallel_mixed_operations(client: AsyncClient) -> None:
    """Смешанные параллельные пополнения/списания"""
    wallet_id = (await client.post("/api/v1/wallets")).json()["id"]
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": "1000.00"},
    )

    async def deposit() -> None:
        await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "DEPOSIT", "amount": "5.00"},
        )

    async def withdraw() -> None:
        await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": "3.00"},
        )

    tasks = []
    for _ in range(50):
        tasks.append(deposit())
        tasks.append(withdraw())
    await asyncio.gather(*tasks)

    # 1000 + 50*5 - 50*3 = 1100.00
    resp = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert Decimal(resp.json()["balance"]) == Decimal("1100.00")