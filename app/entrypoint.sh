#!/bin/bash
set -e

uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level critical &

until curl -s http://localhost:8001/docs > /dev/null; do
  echo "Ожидание запуска FastAPI..."
  sleep 2
done

echo "FastAPI запущен. Запускаем тесты..."

pytest -v --disable-warnings ./app/tests/test.py
