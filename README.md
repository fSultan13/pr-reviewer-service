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
docker build -t pr-reviewer-service .
```

Обратите внимание: `.env` добавлен в `.dockerignore`, поэтому он **не попадает** внутрь образа при сборке.
Переменные окружения нужно передавать контейнеру при запуске.

### 8.2. Применение миграций (в Docker)

Вариант: выполнить миграции внутри контейнера (одиночный запуск):

```bash
docker run --rm \
  --env-file .env \
  pr-reviewer-service \
  alembic upgrade head
```

(Команда переопределяет `CMD` и просто прогоняет миграции.)

### 8.3. Запуск сервиса

Обычный запуск приложения в контейнере:

```bash
docker run --rm \
  --env-file .env \
  -p 8080:8080 \
  pr-reviewer-service
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

Параметры сценария: ~13.8 req/s суммарно по основным эндпоинтам (/pullRequest/create, /pullRequest/reassign,
/pullRequest/merge, /users/getReview).

Результаты:

Всего запросов: 4128

Ошибки: 0 (100% успешных, при требовании ≥ 99.9%)

Средний RPS: ~13.8 (требование: 5 RPS – сервис выдерживает нагрузку с запасом)

Aggregated latency:

- p95: 16 ms
- p99: 21 ms
- p99.9: 31 ms
- max: 81 ms (при лимите 300 ms)

Вывод: сервис при нагрузке, превышающей требуемую (13.8 RPS против 5 RPS), демонстрирует время ответа значительно ниже
300 ms и успешность 100%, что удовлетворяет заявленным SLI с запасом.


### Вывод Locust

Таблица 1 — общая статистика

| Type | Name                         | # reqs | # fails   | Avg | Min | Max | Med | req/s | failures/s |
|------|------------------------------|--------|-----------|-----|-----|-----|-----|-------|------------|
| POST | /pullRequest/create          | 1248   | 0 (0.00%) | 10  | 4   | 55  | 10  | 4.16  | 0.00       |
| POST | /pullRequest/merge           | 1224   | 0 (0.00%) | 7   | 2   | 28  | 7   | 4.08  | 0.00       |
| POST | /pullRequest/reassign        | 818    | 0 (0.00%) | 10  | 4   | 31  | 10  | 2.73  | 0.00       |
| POST | /team/add                    | 5      | 0 (0.00%) | 21  | 3   | 81  | 9   | 0.02  | 0.00       |
| GET  | /users/getReview?user_id=u1  | 99     | 0 (0.00%) | 6   | 2   | 30  | 6   | 0.33  | 0.00       |
| GET  | /users/getReview?user_id=u10 | 97     | 0 (0.00%) | 6   | 1   | 24  | 6   | 0.32  | 0.00       |
| GET  | /users/getReview?user_id=u2  | 77     | 0 (0.00%) | 6   | 2   | 14  | 6   | 0.26  | 0.00       |
| GET  | /users/getReview?user_id=u3  | 70     | 0 (0.00%) | 5   | 2   | 17  | 5   | 0.23  | 0.00       |
| GET  | /users/getReview?user_id=u4  | 85     | 0 (0.00%) | 6   | 2   | 22  | 6   | 0.28  | 0.00       |
| GET  | /users/getReview?user_id=u5  | 86     | 0 (0.00%) | 6   | 2   | 17  | 6   | 0.29  | 0.00       |
| GET  | /users/getReview?user_id=u6  | 75     | 0 (0.00%) | 6   | 2   | 22  | 6   | 0.25  | 0.00       |
| GET  | /users/getReview?user_id=u7  | 78     | 0 (0.00%) | 6   | 2   | 21  | 5   | 0.26  | 0.00       |
| GET  | /users/getReview?user_id=u8  | 86     | 0 (0.00%) | 6   | 2   | 12  | 6   | 0.29  | 0.00       |
| GET  | /users/getReview?user_id=u9  | 80     | 0 (0.00%) | 6   | 2   | 25  | 6   | 0.27  | 0.00       |
|      | **Aggregated**               | 4128   | 0 (0.00%) | 8   | 1   | 81  | 8   | 13.77 | 0.00       |


Таблица 2 — персентили времени ответа

| Type | Name                         | 50% | 66% | 75% | 80% | 90% | 95% | 98% | 99% | 99.9% | 99.99% | 100% | # reqs |
|------|------------------------------|-----|-----|-----|-----|-----|-----|-----|-----|-------|--------|------|--------|
| POST | /pullRequest/create          | 10  | 11  | 12  | 13  | 15  | 18  | 20  | 23  | 40    | 56     | 56   | 1248   |
| POST | /pullRequest/merge           | 7   | 8   | 9   | 9   | 11  | 13  | 15  | 17  | 27    | 28     | 28   | 1224   |
| POST | /pullRequest/reassign        | 10  | 11  | 13  | 13  | 16  | 17  | 19  | 20  | 31    | 31     | 31   | 818    |
| POST | /team/add                    | 9   | 9   | 9   | 81  | 81  | 81  | 81  | 81  | 81    | 81     | 81   | 5      |
| GET  | /users/getReview?user_id=u1  | 6   | 7   | 8   | 8   | 10  | 11  | 13  | 30  | 30    | 30     | 30   | 99     |
| GET  | /users/getReview?user_id=u10 | 6   | 7   | 8   | 8   | 11  | 11  | 13  | 24  | 24    | 24     | 24   | 97     |
| GET  | /users/getReview?user_id=u2  | 6   | 7   | 8   | 8   | 10  | 12  | 14  | 14  | 14    | 14     | 14   | 77     |
| GET  | /users/getReview?user_id=u3  | 5   | 6   | 7   | 7   | 9   | 11  | 13  | 18  | 18    | 18     | 18   | 70     |
| GET  | /users/getReview?user_id=u4  | 6   | 7   | 7   | 8   | 9   | 12  | 18  | 23  | 23    | 23     | 23   | 85     |
| GET  | /users/getReview?user_id=u5  | 6   | 7   | 7   | 8   | 9   | 11  | 13  | 18  | 18    | 18     | 18   | 86     |
| GET  | /users/getReview?user_id=u6  | 6   | 6   | 7   | 7   | 8   | 10  | 14  | 23  | 23    | 23     | 23   | 75     |
| GET  | /users/getReview?user_id=u7  | 5   | 6   | 7   | 7   | 9   | 12  | 17  | 21  | 21    | 21     | 21   | 78     |
| GET  | /users/getReview?user_id=u8  | 6   | 7   | 8   | 8   | 9   | 11  | 12  | 12  | 12    | 12     | 12   | 86     |
| GET  | /users/getReview?user_id=u9  | 6   | 7   | 7   | 8   | 11  | 15  | 24  | 25  | 25    | 25     | 25   | 80     |
|      | **Aggregated**               | 8   | 10  | 11  | 11  | 14  | 16  | 19  | 21  | 31    | 81     | 81   | 4128   |


---


## 11. Лицензия

Проект распространяется под лицензией **MIT** (см. файл `LICENSE`).
