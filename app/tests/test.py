import pytest
import uuid
from httpx import AsyncClient
from loguru import logger

BASE_URL = "http://localhost:8001"


@pytest.mark.asyncio
async def test_create_wallet():
    """Тест на создание нового кошелька."""
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/v1/wallets/")
        response_json = response.json()
        assert response.status_code == 200
        assert "wallet_uuid" in response_json
        assert "balance" in response_json
        assert response_json["balance"] == 0.0
        delete_response = await client.delete(f"/api/v1/wallets/{response_json["wallet_uuid"]}")
        assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_get_wallet_balance():
    """Тест на получение баланса кошелька по его UUID."""
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/v1/wallets/")
        create_response_json = response.json()
        # logger.info(create_response_json["wallet_uuid"])
        balance_response = await client.get(f"/api/v1/wallets/{create_response_json["wallet_uuid"]}")
        balance_json = balance_response.json()
        # logger.info(balance_json["balance"])
        assert balance_response.status_code == 200
        assert "balance" in balance_json
        assert balance_json["balance"] == 0.0

        delete_response = await client.delete(f"/api/v1/wallets/{create_response_json["wallet_uuid"]}")
        assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_list_wallets():
    """Тест на получение списка всех кошельков."""
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/v1/wallets/")
        response_json = response.json()

        assert response.status_code == 200
        assert isinstance(response_json, dict)
        assert "wallets" in response_json
        assert isinstance(response_json["wallets"], list)


@pytest.mark.asyncio
async def test_create_operation_deposit():
    """Тест на создание операции для кошелька депозит."""
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post("/api/v1/wallets/")
        create_response_json = create_response.json()
        wallet_uuid = create_response_json["wallet_uuid"]

        operation_data = {
            "amount": 100.0,
            "operation_type": "DEPOSIT"
        }

        operation_response = await client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation",
            json=operation_data
        )
        operation_json = operation_response.json()

        assert operation_response.status_code == 200
        assert operation_json["amount"] == 100.0
        assert operation_json["operation_type"] == "DEPOSIT"
        logger.info(wallet_uuid)
        delete_response = await client.delete(f"/api/v1/wallets/{wallet_uuid}")
        assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_create_operation_withdrow():
    """Тест на создание операции для кошелька снятие."""
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post("/api/v1/wallets/")
        create_response_json = create_response.json()
        wallet_uuid = create_response_json["wallet_uuid"]

        operation_data = {
            "amount": 100.0,
            "operation_type": "DEPOSIT"
        }

        operation_response = await client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation",
            json=operation_data
        )
        operation_json = operation_response.json()

        assert operation_response.status_code == 200
        assert operation_json["amount"] == 100.0
        assert operation_json["operation_type"] == "DEPOSIT"

        operation_data = {
            "amount": 10.0,
            "operation_type": "WITHDRAW"
        }

        operation_response = await client.post(
            f"/api/v1/wallets/{wallet_uuid}/operation",
            json=operation_data
        )
        operation_json = operation_response.json()
        assert operation_response.status_code == 200
        # assert operation_json["balance"] == 90.0
        assert operation_json["amount"] == 10.0
        assert operation_json["operation_type"] == "WITHDRAW"
        logger.info(operation_json)
        delete_response = await client.delete(f"/api/v1/wallets/{wallet_uuid}")
        assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_delete_wallet():
    """Тест на удаление кошелька по UUID."""
    async with AsyncClient(base_url=BASE_URL) as client:
        create_response = await client.post("/api/v1/wallets/")
        create_response_json = create_response.json()
        wallet_uuid = create_response_json["wallet_uuid"]

        delete_response = await client.delete(f"/api/v1/wallets/{wallet_uuid}")

        assert delete_response.status_code == 200

        second_delete_response = await client.delete(f"/api/v1/wallets/{wallet_uuid}")
        assert second_delete_response.status_code == 404
        assert second_delete_response.json()["detail"] == "Wallet not found"


@pytest.mark.asyncio
async def test_create_wallet():
    """Тест на создание нового кошелька."""
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/v1/wallets/")
        response_json = response.json()

        assert response.status_code == 200
        assert "wallet_uuid" in response_json
        assert "balance" in response_json
        assert response_json["balance"] == 0.0

        delete_response = await client.delete(f"/api/v1/wallets/{response_json['wallet_uuid']}")
        assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_create_wallet_operation_invalid_wallet():
    """Тест на попытку создания операции для несуществующего кошелька."""
    invalid_wallet_uuid = str(uuid.uuid4())

    async with AsyncClient(base_url=BASE_URL) as client:
        operation_data = {
            "amount": 100.0,
            "operation_type": "DEPOSIT"
        }

        response = await client.post(f"/api/v1/wallets/{invalid_wallet_uuid}/operation", json=operation_data)
        assert response.status_code == 404
        assert response.json()["detail"] == "Кошелек не найден"


@pytest.mark.asyncio
async def test_create_wallet_operation_invalid_data():
    """Тест на создание операции с некорректными данными."""
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/v1/wallets/")
        wallet_uuid = response.json()["wallet_uuid"]

        invalid_operation_data = {
            "amount": "не число",  # Некорректное значение
            "operation_type": "UNKNOWN_TYPE"  # Несуществующий тип операции
        }

        response = await client.post(f"/api/v1/wallets/{wallet_uuid}/operation", json=invalid_operation_data)
        assert response.status_code == 422  # Ошибка валидации данных

        delete_response = await client.delete(f"/api/v1/wallets/{wallet_uuid}")
        assert delete_response.status_code == 200


@pytest.mark.asyncio
async def test_get_wallet_balance_invalid_wallet():
    """Тест на попытку получения баланса несуществующего кошелька."""
    invalid_wallet_uuid = str(uuid.uuid4())

    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get(f"/api/v1/wallets/{invalid_wallet_uuid}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Кошелек не найден"


@pytest.mark.asyncio
async def test_delete_wallet_twice():
    """Тест на двойное удаление кошелька."""
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/v1/wallets/")
        wallet_uuid = response.json()["wallet_uuid"]

        delete_response = await client.delete(f"/api/v1/wallets/{wallet_uuid}")
        assert delete_response.status_code == 200

        second_delete_response = await client.delete(f"/api/v1/wallets/{wallet_uuid}")
        assert second_delete_response.status_code == 404
        assert second_delete_response.json()["detail"] == "Wallet not found"


@pytest.mark.asyncio
async def test_list_wallets_empty():
    """Тест на получение списка кошельков, если их нет."""
    async with AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/v1/wallets/")
        response_json = response.json()

        assert response.status_code == 200
        assert isinstance(response_json, dict)
        assert "wallets" in response_json
        assert isinstance(response_json["wallets"], list)
        assert len(response_json["wallets"]) == 0  # Проверяем, что кошельков нет
