# Wallet API

REST API для работы с кошельками пользователей на FastAPI + PostgreSQL.

## Стек

- **FastAPI** — асинхронный веб-фреймворк
- **SQLAlchemy 2.0 (async)** + **asyncpg** — работа с БД
- **Alembic** — миграции
- **PostgreSQL 16** — база данных
- **Docker / docker-compose** — контейнеризация
- **pytest** + **pytest-asyncio** + **httpx** — тесты

## Возможности

- Изменение баланса кошелька (DEPOSIT / WITHDRAW)
- Получение текущего баланса
- Корректная работа при конкурентных запросах
- Запрет отрицательного баланса на уровне БД (CheckConstraint)
- Валидация входных данных через Pydantic
- Асинхронная работа с БД

## Endpoints

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/wallets` | Создать кошелёк (вспомогательный) |
| POST | `/api/v1/wallets/{wallet_id}/operation` | DEPOSIT или WITHDRAW |
| GET | `/api/v1/wallets/{wallet_id}` | Получить баланс |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI |

### Пример запроса операции

```http
POST /api/v1/wallets/<WALLET_UUID>/operation
Content-Type: application/json

{
  "operation_type": "DEPOSIT",
  "amount": 1000
}
```

### Коды ответов

| Код | Когда |
|-----|-------|
| 200 | Успех |
| 201 | Кошелёк создан |
| 404 | Кошелёк не найден |
| 409 | Недостаточно средств для WITHDRAW |
| 422 | Ошибка валидации |

## Запуск

### Требования

- Docker Desktop
- docker-compose

### Одна команда

```bash
docker compose up --build
```

Приложение будет доступно на http://127.0.0.1:8000

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Остановить:

```bash
docker compose down
```

Остановить и удалить данные:

```bash
docker compose down -v
```

## Тесты

```bash
pytest
```

Покрытие:

- CRUD-операции эндпоинтов
- Валидация входных данных (422)
- Несуществующий кошелёк (404)
- Недостаток средств (409)
- **Конкурентность**: параллельные депозиты, параллельные списания (проверка, что баланс не уходит в минус, количество успехов/конфликтов строго детерминировано), смешанные параллельные операции

## Конкурентность

Для защиты от гонок при параллельных изменениях одного кошелька используется **пессимистичная блокировка строки** (`SELECT ... FOR UPDATE`) внутри транзакции:

1. Транзакция A открывается и делает `SELECT ... FOR UPDATE` — строка блокируется.
2. Транзакция B в это же время пытается сделать то же — она ждёт, пока A не закоммитит.
3. После коммита A — B читает уже обновлённый баланс.
4. Дополнительно на уровне БД стоит `CHECK (balance >= 0)` — последняя линия защиты.

Это гарантирует, что read-modify-write не пересекается, и баланс никогда не уходит в минус.

## Структура проекта

```
wallet_test/
├── alembic/                  # Миграции
│   ├── versions/
│   └── env.py
├── app/
│   ├── api/v1/wallets.py     # Роутеры
│   ├── models/wallet.py      # ORM-модели
│   ├── repositories/wallet.py # Работа с БД (атомарные операции)
│   ├── schemas/wallet.py     # Pydantic-схемы
│   ├── services/wallet.py    # Бизнес-логика
│   ├── config.py             # Настройки
│   ├── database.py           # Engine + session
│   └── main.py               # FastAPI-приложение
├── docker/
│   └── entrypoint.sh         # Ожидание БД + миграции + uvicorn
├── tests/
│   ├── conftest.py
│   ├── test_wallets.py
│   └── test_concurrency.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|-----------|--------------|----------|
| POSTGRES_USER | wallet_user | Пользователь БД |
| POSTGRES_PASSWORD | wallet_password | Пароль |
| POSTGRES_DB | wallet_db | Имя БД |
| POSTGRES_HOST | localhost (локально) / db (в docker) | Хост БД |
| POSTGRES_PORT | 5432 (локально) / 5432 (в docker) | Порт |
| DEBUG | false | SQL echo |

## Примечания

- Проект собран под Python 3.14 (локально) и 3.13 (в Docker образе — из соображений стабильности доступных wheel-пакетов).
- Используется `Numeric(18, 2)` для баланса — точная арифметика без ошибок float.
- Все миграции применяются автоматически при старте контейнера `app`.