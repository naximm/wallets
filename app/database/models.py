import datetime
import uuid
from enum import Enum

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, Enum as SqlAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy. Наследуется от DeclarativeBase,
    предоставляющего функциональность для определения моделей.
    """
    pass


class OperationType(str, Enum):
    """
    Перечисление для типов операций.

    Attributes:
        DEPOSIT: Пополнение баланса
        WITHDRAW: Снятие средств

    Methods:
        _missing_(cls, value): Обрабатывает неправильные значения для операций и выдает ошибку
    """
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"

    @classmethod
    def _missing_(cls, value):
        raise ValueError(f"Invalid operation_type '{value}'. Allowed values: {', '.join(cls.__members__.keys())}")


class Wallet(Base):
    """
    Модель для кошелька.

    Attributes:
        wallet_uuid: Уникальный идентификатор кошелька
        balance: Баланс кошелька

    Relationships:
        operations: Операции, связанные с этим кошельком
    """
    __tablename__ = 'wallets'

    wallet_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    balance = Column(Numeric(precision=10, scale=2), nullable=False, default=0.00)

    operations = relationship('Operation', back_populates='wallet', cascade="all, delete-orphan")


class Operation(Base):
    """
    Модель для операции над кошельком.

    Attributes:
        operation_id: Уникальный идентификатор операции
        wallet_uuid: Идентификатор кошелька, с которым связана операция
        operation_type: Тип операции (пополнение или снятие)
        amount: Сумма операции
        timestamp: Время выполнения операции

    Relationships:
        wallet: Кошелек, с которым связана операция
    """
    __tablename__ = 'operations'

    operation_id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_uuid = Column(UUID(as_uuid=True), ForeignKey('wallets.wallet_uuid', ondelete='CASCADE'), nullable=False)
    operation_type = Column(SqlAlchemyEnum(OperationType), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    wallet = relationship('Wallet', back_populates='operations', passive_deletes=True)
