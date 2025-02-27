import datetime
import uuid
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import Wallet, Operation
from ..schemas.operation import OperationRequest, OperationType
from ..schemas.wallet import WalletBalanceResponse


async def get_wallet_by_uuid(wallet_uuid: uuid.UUID, db: AsyncSession, for_update: bool = False) -> Wallet:
    """
    Получает кошелек по UUID из базы данных

    Args:
        wallet_uuid (uuid.UUID): UUID кошелька
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных
        for_update (bool): Если True, блокирует строку для предотвращения гонки данных

    Returns:
        Wallet: Объект кошелька из базы данных

    Exceptions:
        HTTPException: В случае, если кошелек не найден
        SQLAlchemyError: В случае ошибки базы данных
        Exception: В случае неожиданной ошибки
    """
    try:
        stmt = select(Wallet).filter(Wallet.wallet_uuid == wallet_uuid)

        if for_update:
            stmt = stmt.with_for_update()

        result = await db.execute(stmt)
        wallet = result.scalar_one_or_none()
        return wallet

    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error during wallet retrieval")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def create_wallet_operation(wallet_uuid: uuid.UUID, operation: OperationRequest, db: AsyncSession):
    """
    Выполняет операцию пополнения или снятия средств с кошелька.

    Args:
        wallet_uuid (uuid.UUID): UUID кошелька
        operation (OperationRequest): Данные операции (тип и сумма)
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных

    Returns:
        dict: Информацию о выполненной операции, включая UUID кошелька, тип операции, сумму и новый баланс

    Exceptions:
        HTTPException: В случае ошибки при операциях (недостаточно средств или ошибка базы данных)
        ValueError: В случае недопустимого значения суммы операции
        SQLAlchemyError: В случае ошибки базы данных
        Exception: В случае неожиданной ошибки
    """
    try:
        wallet = await get_wallet_by_uuid(wallet_uuid, db, for_update=True)
        if wallet is None:
            return None

        if operation.operation_type == OperationType.DEPOSIT:
            wallet.balance += operation.amount
        elif operation.operation_type == OperationType.WITHDRAW:
            if wallet.balance < operation.amount:
                raise HTTPException(status_code=400, detail="Insufficient funds")
            wallet.balance -= operation.amount

        # Создаем объект операции и сохраняем в базу данных
        new_operation = Operation(
            wallet_uuid=wallet_uuid,
            operation_type=operation.operation_type,
            amount=operation.amount,
            timestamp=datetime.datetime.utcnow()  # Добавление времени операции
        )
        db.add(new_operation)
        await db.commit()
        await db.refresh(wallet)

        return {
            "wallet_uuid": wallet_uuid,
            "operation_type": operation.operation_type,
            "amount": operation.amount,
            "new_balance": str(wallet.balance)
        }

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error during wallet operation")
    except ValueError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid operation amount")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def get_wallet_balance(wallet_uuid: uuid.UUID, db: AsyncSession) -> WalletBalanceResponse | None:
    """
    Получает баланс кошелька по UUID.

    Args:
        wallet_uuid (uuid.UUID): UUID кошелька
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных

    Returns:
        WalletBalanceResponse: Объект с UUID кошелька и его текущим балансом

    Exceptions:
        HTTPException: В случае ошибки при получении баланса
        SQLAlchemyError: В случае ошибки базы данных
        Exception: В случае неожиданной ошибки
    """
    try:
        wallet = await get_wallet_by_uuid(wallet_uuid, db)
        if wallet is None:
            return None
        return WalletBalanceResponse(wallet_uuid=wallet.wallet_uuid, balance=wallet.balance)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def create_new_wallet(db: AsyncSession) -> dict:
    """
    Создает новый кошелек с начальным балансом 0.00

    Args:
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных

    Returns:
        dict: Информацию о созданном кошельке (UUID и баланс)

    Exceptions:
        HTTPException: В случае ошибки при создании кошелька
        SQLAlchemyError: В случае ошибки базы данных
        Exception: В случае неожиданной ошибки
    """
    try:
        wallet_uuid = uuid.uuid4()
        wallet = Wallet(wallet_uuid=wallet_uuid, balance=0.00)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)

        return {
            "wallet_uuid": wallet.wallet_uuid,
            "balance": wallet.balance
        }
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error during wallet creation")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def get_list_wallets(db: AsyncSession) -> list:
    """
    Получает список всех кошельков с их балансами

    Args:
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных

    Returns:
        list: Список объектов `WalletBalanceResponse`, содержащих UUID и баланс каждого кошелька

    Exceptions:
        HTTPException: В случае ошибки при получении списка кошельков
        SQLAlchemyError: В случае ошибки базы данных
        Exception: В случае неожиданной ошибки
    """
    try:
        result = await db.execute(select(Wallet))
        wallets = result.scalars().all()
        return [WalletBalanceResponse(wallet_uuid=wallet.wallet_uuid, balance=wallet.balance) for wallet in wallets]
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error during wallet list retrieval")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


async def delete_wallet_by_uuid(wallet_uuid: uuid.UUID, db: AsyncSession) -> dict:
    """
    Удаляет кошелек по UUID из базы данных.

    Args:
        wallet_uuid (uuid.UUID): UUID кошелька для удаления
        db (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных

    Returns:
        dict: Информацию о завершении операции (например, сообщение об успешном удалении)

    Exceptions:
        HTTPException: В случае ошибки при удалении кошелька
        SQLAlchemyError: В случае ошибки базы данных
        Exception: В случае неожиданной ошибки
    """
    try:
        # Ищем кошелек по UUID
        wallet = await get_wallet_by_uuid(wallet_uuid, db)
        if not wallet:
            return {"message": "Wallet not found", "wallet_uuid": wallet_uuid}

        await db.delete(wallet)
        await db.commit()

        return {"message": "Wallet successfully deleted", "wallet_uuid": wallet_uuid}

    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error during wallet deletion")

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


