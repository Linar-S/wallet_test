import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet


class WalletRepository:
    """Слой доступа к данным кошельков"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, wallet_id: uuid.UUID) -> Wallet | None:
        """Возвращает кошелёк по id или None"""
        stmt = select(Wallet).where(Wallet.id == wallet_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, wallet_id: uuid.UUID) -> Wallet | None:
        """Возвращает кошелёк по id с блокировкой строки

        Блокирует конкурирующие транзакции до фиксации или отката текущей
        """
        stmt = select(Wallet).where(Wallet.id == wallet_id).with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, wallet_id: uuid.UUID | None = None) -> Wallet:
        """Создаёт новый кошелёк с нулевым балансом"""
        wallet = Wallet(id=wallet_id) if wallet_id else Wallet()
        self._session.add(wallet)
        await self._session.flush()
        await self._session.refresh(wallet)
        return wallet

    async def update_balance(
        self,
        wallet: Wallet,
        new_balance: Decimal,
    ) -> Wallet:
        """Сохраняет новый баланс и обновляет объект из БД"""
        wallet.balance = new_balance
        await self._session.flush()
        await self._session.refresh(wallet)
        return wallet