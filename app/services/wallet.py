import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet
from app.repositories.wallet import WalletRepository


class WalletNotFoundError(Exception):
    """Выбрасывается, когда кошелёк не существует"""


class InsufficientFundsError(Exception):
    """Выбрасывается, когда сумма списания превышает текущий баланс"""


class WalletService:
    """Бизнес-логика операций с кошельками"""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = WalletRepository(session)

    async def get_wallet(self, wallet_id: uuid.UUID) -> Wallet:
        """Возвращает кошелёк или выбрасывает WalletNotFoundError"""
        wallet = await self._repo.get_by_id(wallet_id)
        if wallet is None:
            raise WalletNotFoundError(wallet_id)
        return wallet

    async def create_wallet(self, wallet_id: uuid.UUID | None = None) -> Wallet:
        """Создаёт новый пустой кошелёк"""
        wallet = await self._repo.create(wallet_id)
        await self._session.commit()
        return wallet

    async def apply_operation(
        self,
        wallet_id: uuid.UUID,
        operation_type: str,
        amount: Decimal,
    ) -> Wallet:
        """Атомарно применяет DEPOSIT или WITHDRAW с блокировкой строки"""
        wallet = await self._repo.get_by_id_for_update(wallet_id)
        if wallet is None:
            raise WalletNotFoundError(wallet_id)

        if operation_type == "DEPOSIT":
            new_balance = wallet.balance + amount
        elif operation_type == "WITHDRAW":
            if wallet.balance < amount:
                raise InsufficientFundsError(
                    f"Wallet {wallet_id} has {wallet.balance}, "
                    f"cannot withdraw {amount}"
                )
            new_balance = wallet.balance - amount
        else:
            raise ValueError(f"Unknown operation_type: {operation_type}")

        wallet = await self._repo.update_balance(wallet, new_balance)
        await self._session.commit()
        return wallet