# pr-reviewer-service

Сервис для автоматического назначения ревьюеров на Pull Request’ы внутри команды.
Стек: **FastAPI**, **SQLAlchemy 2**, **PostgreSQL**, **Alembic**, **Poetry**, **Pytest**.

---

## 1. Требования

* Python **3.12+**
* [Poetry](https://python-poetry.org/) **2.x**
* PostgreSQL (любая актуальная версия)
* `make` (по желанию, для удобного запуска команд)
* Docker (по желанию, для контейнерного запуска)

---

## 2. Настройка окружения

### 2.1. Клонирование проекта

```bash
git clone <url-репозитория> pr-reviewer-service
cd pr-reviewer-service
```

(если проект уже распакован — просто перейдите в корень, где лежат `pyproject.toml`, `Dockerfile`, `Makefile` и т.д.)

### 2.2. Файл окружения `.env`

В корне проекта уже есть пример: **`.env.example`**.
Скопируйте его и отредактируйте под своё окружение:

```bash
cp .env.example .env
```

Пример содержимого:

```env
PROJECT_NAME="Python pr reviewer service"

# Основная БД
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=pr_reviewer_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=xxXX1234

# Тестовая БД (для pytest)
POSTGRES_SERVER_TEST=localhost
POSTGRES_PORT_TEST=5432
POSTGRES_DB_TEST=pr_reviewer_db_test
POSTGRES_USER_TEST=postgres
POSTGRES_PASSWORD_TEST=xxXX1234

SECRET_KEY=local
```

> * Задайте свои реальные значения пароля и `SECRET_KEY`, особенно для продакшена.
> * При необходимости можно добавить переменную `API_V1_STR="/api/v1"`, чтобы повесить всё API на префикс.

### 2.3. Создание баз данных

Создайте базы `pr_reviewer_db` и `pr_reviewer_db_test` (или свои, если меняли названия в `.env`).

Пример через `psql`:

```bash
psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE pr_reviewer_db;"
psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE pr_reviewer_db_test;"
```

---

## 3. Установка зависимостей

Из корня проекта:

```bash
poetry install
```

Активируйте виртуальное окружение (если Poetry не сделает этого сам):

```bash
poetry shell
```

---

## 4. Миграции БД

В проекте используется Alembic, конфигурация уже лежит в `alembic.ini`, а миграции — в папке `migrations/`.

Применить миграции можно так:

```bash
make migrate
# или напрямую
poetry run alembic upgrade head
```

---

## 5. Запуск приложения (локально)

Запуск через `Makefile`:

```bash
make run
```

Это эквивалентно:

```bash
poetry run uvicorn app.main:app --reload --port 8080
```

После запуска приложение доступно по адресу:

* Swagger UI: `http://localhost:8080/docs`
* OpenAPI JSON: `http://localhost:8080/openapi`

(Если вы зададите `API_V1_STR`, пути будут с соответствующим префиксом.)

---

## 6. Тесты

Тесты используют **отдельную тестовую базу**, параметры которой задаются переменными `POSTGRES_*_TEST` из `.env`.

Убедитесь, что тестовая база создана, затем выполните:

```bash
make test
# или
poetry run pytest -v
```

---

## 7. Линтеры и форматирование

В проекте настроены **black**, **isort**, **ruff**. Все команды собраны в `Makefile`:

```bash
# Форматирование кода (black + isort)
make format

# Линтер (ruff)
make lint

# Полная проверка: форматирование, линтеры, тесты
make check
```

---

## 8. Запуск через Docker

### 8.1. Сборка образа

Из корня проекта:

```bash
docker compose build
```

### 8.2. Запуск сервиса

Обычный запуск приложения в контейнере:

```bash
docker compose up
```

После этого сервис доступен по:

* `http://localhost:8080/docs`

---

## 9. Полезные команды (сводка)

Из корня проекта:

```bash
# Установка зависимостей
poetry install

# Миграции
make migrate

# Запуск приложения
make run

# Тесты
make test

# Форматирование
make format

# Линтеры
make lint

# Все проверки: форматирование + линтеры + тесты
make check
```

---

## Нагрузочное тестирование

Нагрузочное тестирование проводилось с помощью Locust.

```bash
# Команда для запуска
locust -f locustfile.py \
  --headless \
  -u 5 \
  -r 1 \
  -t 5m \
  --host http://localhost:8080
```

Параметры сценария: ~11.9 req/s суммарно по основным эндпоинтам (/pullRequest/create, /pullRequest/reassign,
/pullRequest/merge, /users/getReview).

Результаты:

Всего запросов: 3569

Ошибки: 0 (100% успешных, при требовании ≥ 99.9%)

Средний RPS: ~11.9 (требование: 5 RPS – сервис выдерживает нагрузку с запасом)

Aggregated latency:

- p95: 14 ms
- p99: 17 ms
- p99.9: 35 ms
- max: 49 ms (при лимите 300 ms)

Вывод: сервис при нагрузке, превышающей требуемую (11.9 RPS против 5 RPS), демонстрирует время ответа значительно ниже
300 ms и успешность 100%, что удовлетворяет заявленным SLI с запасом.

### Вывод Locust

Таблица 1 — общая статистика

| Type | Name                         | # reqs | # fails   | Avg | Min | Max | Med | req/s | failures/s |
|------|------------------------------|--------|-----------|-----|-----|-----|-----|-------|------------|
| POST | /pullRequest/create          | 1122   | 0 (0.00%) | 9   | 3   | 36  | 9   | 3.74  | 0.00       |
| POST | /pullRequest/merge           | 1104   | 0 (0.00%) | 7   | 2   | 36  | 7   | 3.68  | 0.00       |
| POST | /pullRequest/reassign        | 205    | 0 (0.00%) | 5   | 2   | 49  | 5   | 0.68  | 0.00       |
| POST | /team/add                    | 5      | 0 (0.00%) | 6   | 3   | 16  | 5   | 0.02  | 0.00       |
| POST | /team/deactivateUsers        | 358    | 0 (0.00%) | 7   | 3   | 21  | 7   | 1.19  | 0.00       |
| GET  | /users/getReview?user_id=u1  | 65     | 0 (0.00%) | 4   | 2   | 9   | 4   | 0.22  | 0.00       |
| GET  | /users/getReview?user_id=u10 | 73     | 0 (0.00%) | 4   | 2   | 12  | 4   | 0.24  | 0.00       |
| GET  | /users/getReview?user_id=u2  | 72     | 0 (0.00%) | 5   | 2   | 16  | 5   | 0.24  | 0.00       |
| GET  | /users/getReview?user_id=u3  | 69     | 0 (0.00%) | 5   | 2   | 12  | 4   | 0.23  | 0.00       |
| GET  | /users/getReview?user_id=u4  | 74     | 0 (0.00%) | 5   | 2   | 10  | 5   | 0.25  | 0.00       |
| GET  | /users/getReview?user_id=u5  | 82     | 0 (0.00%) | 5   | 2   | 12  | 4   | 0.27  | 0.00       |
| GET  | /users/getReview?user_id=u6  | 80     | 0 (0.00%) | 4   | 1   | 10  | 4   | 0.27  | 0.00       |
| GET  | /users/getReview?user_id=u7  | 80     | 0 (0.00%) | 4   | 2   | 8   | 5   | 0.27  | 0.00       |
| GET  | /users/getReview?user_id=u8  | 86     | 0 (0.00%) | 4   | 2   | 12  | 4   | 0.29  | 0.00       |
| GET  | /users/getReview?user_id=u9  | 94     | 0 (0.00%) | 4   | 2   | 9   | 4   | 0.31  | 0.00       |
|      | **Aggregated**               | 3569   | 0 (0.00%) | 7   | 1   | 49  | 7   | 11.91 | 0.00       |

Таблица 2 — персентили времени ответа

| Type | Name                         | 50% | 66% | 75% | 80% | 90% | 95% | 98% | 99% | 99.9% | 99.99% | 100% | # reqs |
|------|------------------------------|-----|-----|-----|-----|-----|-----|-----|-----|-------|--------|------|--------|
| POST | /pullRequest/create          | 9   | 10  | 11  | 12  | 14  | 16  | 17  | 19  | 35    | 37     | 37   | 1122   |
| POST | /pullRequest/merge           | 7   | 8   | 9   | 9   | 11  | 13  | 15  | 15  | 30    | 36     | 36   | 1104   |
| POST | /pullRequest/reassign        | 5   | 6   | 6   | 7   | 8   | 9   | 11  | 15  | 50    | 50     | 50   | 205    |
| POST | /team/add                    | 5   | 6   | 6   | 17  | 17  | 17  | 17  | 17  | 17    | 17     | 17   | 5      |
| POST | /team/deactivateUsers        | 7   | 8   | 9   | 9   | 11  | 12  | 14  | 18  | 21    | 21     | 21   | 358    |
| GET  | /users/getReview?user_id=u1  | 4   | 5   | 6   | 6   | 8   | 8   | 8   | 9   | 9     | 9      | 9    | 65     |
| GET  | /users/getReview?user_id=u10 | 4   | 5   | 5   | 6   | 7   | 8   | 9   | 12  | 12    | 12     | 12   | 73     |
| GET  | /users/getReview?user_id=u2  | 5   | 6   | 6   | 6   | 8   | 9   | 10  | 16  | 16    | 16     | 16   | 72     |
| GET  | /users/getReview?user_id=u3  | 4   | 5   | 6   | 7   | 9   | 9   | 10  | 13  | 13    | 13     | 13   | 69     |
| GET  | /users/getReview?user_id=u4  | 5   | 6   | 7   | 7   | 8   | 9   | 10  | 11  | 11    | 11     | 11   | 74     |
| GET  | /users/getReview?user_id=u5  | 4   | 5   | 6   | 6   | 8   | 9   | 10  | 13  | 13    | 13     | 13   | 82     |
| GET  | /users/getReview?user_id=u6  | 4   | 5   | 6   | 6   | 8   | 9   | 9   | 10  | 10    | 10     | 10   | 80     |
| GET  | /users/getReview?user_id=u7  | 5   | 5   | 6   | 6   | 7   | 8   | 8   | 9   | 9     | 9      | 9    | 80     |
| GET  | /users/getReview?user_id=u8  | 5   | 5   | 6   | 6   | 8   | 8   | 11  | 13  | 13    | 13     | 13   | 86     |
| GET  | /users/getReview?user_id=u9  | 4   | 5   | 6   | 6   | 7   | 8   | 8   | 9   | 9     | 9      | 9    | 94     |
|      | **Aggregated**               | 7   | 8   | 9   | 10  | 12  | 14  | 16  | 17  | 35    | 50     | 50   | 3569   |

---

## 11. Лицензия

Проект распространяется под лицензией **MIT** (см. файл `LICENSE`).
