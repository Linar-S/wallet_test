import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.wallet import (
    OperationType,
    WalletOperationRequest,
    WalletResponse,
)
from app.services.wallet import (
    InsufficientFundsError,
    WalletNotFoundError,
    WalletService,
)

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])


def get_wallet_service(
    session: AsyncSession = Depends(get_session),
) -> WalletService:
    """Предоставляет WalletService, привязанный к текущей сессии БД"""
    return WalletService(session)


@router.post(
    "/{wallet_id}/operation",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
)
async def wallet_operation(
    wallet_id: uuid.UUID,
    payload: WalletOperationRequest,
    service: WalletService = Depends(get_wallet_service),
) -> WalletResponse:
    """Пополняет кошелёк или списывает средства"""
    try:
        wallet = await service.apply_operation(
            wallet_id=wallet_id,
            operation_type=payload.operation_type.value,
            amount=payload.amount,
        )
    except WalletNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        )
    except InsufficientFundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    return WalletResponse.model_validate(wallet)


@router.get(
    "/{wallet_id}",
    response_model=WalletResponse,
    status_code=status.HTTP_200_OK,
)
async def get_wallet(
    wallet_id: uuid.UUID,
    service: WalletService = Depends(get_wallet_service),
) -> WalletResponse:
    """Возвращает текущий баланс кошелька"""
    try:
        wallet = await service.get_wallet(wallet_id)
    except WalletNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        )
    return WalletResponse.model_validate(wallet)


@router.post(
    "",
    response_model=WalletResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_wallet(
    service: WalletService = Depends(get_wallet_service),
) -> WalletResponse:
    """Создаёт новый кошелёк """
    wallet = await service.create_wallet()
    return WalletResponse.model_validate(wallet)