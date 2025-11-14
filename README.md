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

> ⚠️ **Важно:**
>
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

## 10. Лицензия

Проект распространяется под лицензией **MIT** (см. файл `LICENSE`).
