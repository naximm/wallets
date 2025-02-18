import os
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from app.database.models import Base


def get_database_url():
    """
    Получает строку подключения к базе данных PostgreSQL из переменных окружения

    Args:
        None

    Returns:
        str: Строка подключения к базе данных

    Exceptions:
        ValueError: В случае, если какая-либо из переменных окружения не установлена
    """
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")
    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_pass = os.getenv("POSTGRES_PASSWORD")

    if not all([db_host, db_port, db_name, db_user, db_pass]):
        raise ValueError("Не все необходимые переменные окружения установлены")

    return f"postgresql+asyncpg://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"


ENGINE = create_async_engine(get_database_url())
ASYNC_SESSIONLOCAL = sessionmaker(bind=ENGINE, class_=AsyncSession, expire_on_commit=False)
# logger.info(get_database_url())


async def init_db():
    """
    Инициализирует базу данных, создавая все таблицы, если они не существуют

    Args:
        None

    Returns:
        None

    Exceptions:
        HTTPException: В случае ошибки при выполнении операции с базой данных
        SQLAlchemyError: В случае ошибки SQLAlchemy
    """
    try:
        async with ENGINE.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("База данных успешно инициализирована")
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных при инициализации")
    except Exception as e:
        logger.error(f"Неизвестная ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Неизвестная ошибка: {str(e)}")


async def get_db():
    """
    Генератор сессий базы данных для использования в запросах

    Args:
        None

    Returns:
        AsyncSession: Сессия для работы с базой данных

    Exceptions:
        SQLAlchemyError: В случае ошибки SQLAlchemy при создании сессии
        Exception: В случае неожиданной ошибки при создании сессии
    """
    try:
        database = ASYNC_SESSIONLOCAL()
        yield database
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных при создании сессии: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка базы данных при создании сессии")
    finally:
        try:
            await database.close()
        except Exception as e:
            logger.warning(f"Ошибка при закрытии сессии: {str(e)}")
