from enum import Enum
from pydantic import BaseModel, condecimal


class OperationType(str, Enum):
    """
    Перечисление для типов операций.

    Attributes:
        DEPOSIT: Операция пополнения баланса.
        WITHDRAW: Операция снятия средств.
    """
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class OperationRequest(BaseModel):
    """
    Модель запроса операции над кошельком.

    Attributes:
        operation_type: Тип операции (пополнение или снятие).
        amount: Сумма операции (должна быть больше 0, с точностью до 2 знаков после запятой).
    """
    operation_type: OperationType
    amount: condecimal(gt=0, max_digits=20, decimal_places=2)
