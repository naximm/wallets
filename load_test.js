import { check } from 'k6';
import http from 'k6/http';
import { randomUUID } from 'k6/crypto';

// Генерация случайного UUID для кошелька
const walletUuid = "cab3ca61-1eb1-41a6-9323-999882cd1cc0"; // Используйте свой UUID

export let options = {
  vus: 2000, // количество виртуальных пользователей
  duration: '1m', // продолжительность теста
  rps: 2000, // максимальное количество запросов в секунду
};

export default function () {
  const payload = JSON.stringify({
    operation_type: "DEPOSIT",
    amount: 1,
  });

  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  const res = http.post(`http://0.0.0.0:8001/api/v1/wallets/${walletUuid}/operation`, payload, { headers });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response body contains new_balance': (r) => r.body.includes('new_balance'),
  });
}
