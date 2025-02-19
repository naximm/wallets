import uuid
from pydantic import BaseModel
from typing import List


class WalletBalanceResponse(BaseModel):
    """
    Модель ответа с балансом кошелька.

    Attributes:
        wallet_uuid: Уникальный идентификатор кошелька.
        balance: Текущий баланс кошелька.
    """
    wallet_uuid: uuid.UUID
    balance: float


class WalletListResponse(BaseModel):
    """
    Модель ответа с списком всех кошельков.

    Attributes:
        wallets: Список кошельков с их балансами.
    """
    wallets: List[WalletBalanceResponse]
