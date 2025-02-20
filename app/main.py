import uuid
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from .database.crud import create_new_wallet, get_list_wallets, get_wallet_balance, \
    create_wallet_operation, delete_wallet_by_uuid
from .database.database import get_db, init_db
from .schemas.operation import OperationRequest
from .schemas.wallet import WalletListResponse

app = FastAPI(title="wallets")

app.state.db_initialized = False


@app.on_event("startup")
async def startup_event():
    """
    Событие старта приложения, выполняется при запуске.

    Инициализирует базу данных и устанавливает флаг db_initialized в True,
    чтобы индикатор инициализации базы данных был готов к обработке запросов.
    """
    await init_db()
    app.state.db_initialized = True


@app.post("/api/v1/wallets/{wallet_uuid}/operation")
async def create_operation(wallet_uuid: uuid.UUID, operation: OperationRequest, db: AsyncSession = Depends(get_db)):
    """
    Операция для указанного кошелька.

    Запрос выполняет операцию депозит/снятие для указанного кошелька.
    Проверяет тип операции и соответствующие условия
    """
    try:
        operation = await create_wallet_operation(wallet_uuid, operation, db)
        if operation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
        return operation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unknown error {e}")


@app.get("/api/v1/wallets/{wallet_uuid}")
async def get_balance(wallet_uuid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Получение баланса указанного кошелька.

    Возвращает текущий баланс для указанного кошелька по его UUID.
    """
    try:
        balance = await get_wallet_balance(wallet_uuid, db)
        if balance is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
        return balance
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unknown error: {str(e)}")


@app.get("/api/v1/wallets/")
async def list_wallets(db: AsyncSession = Depends(get_db)):
    """
    Получение списка всех кошельков.

    Возвращает список всех кошельков с их балансами.
    """
    try:
        wallets = await get_list_wallets(db)
        return WalletListResponse(wallets=wallets)
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unknown error: {str(e)}")


@app.post("/api/v1/wallets/")
async def create_wallet(db: AsyncSession = Depends(get_db)):
    """
    Создание нового кошелька.

    Принимает запрос на создание нового кошелька и возвращает его UUID и начальный баланс.
    """
    try:
        return await create_new_wallet(db)
    except SQLAlchemyError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unknown error: {str(e)}")


@app.delete("/api/v1/wallets/{wallet_uuid}")
async def delete_wallet(wallet_uuid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Удаление кошелька.

    Удаляет кошелек по UUID.
    """
    try:
        result = await delete_wallet_by_uuid(wallet_uuid, db)
        if "Wallet not found" in result["message"]:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])

        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unknown error: {str(e)}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
