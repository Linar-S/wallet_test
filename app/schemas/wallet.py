import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OperationType(str, Enum):
    """Доступные операции с кошельком"""

    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class WalletOperationRequest(BaseModel):
    """Тело запроса на изменение баланса кошелька"""

    operation_type: OperationType
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


class WalletResponse(BaseModel):
    """Представление кошелька"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    balance: Decimal
    created_at: datetime
    updated_at: datetime