# Архитектура приложения 

## 1. Входной слой (HTTP API)

**Файлы и модули:**

* `app/main.py`
* `app/api/routers/*.py`
* `app/api/deps.py`

**Что здесь происходит:**

* `main.py`:

  * создаёт `FastAPI`-приложение,
  * задаёт OpenAPI URL (`/api/v1/openapi`),
  * подключает общий `api_router` с префиксом `settings.API_V1_STR` (по умолчанию ``).


* `app/api/routers/`:

  * `team_router.py` — эндпоинты управления командами;
  * `user_router.py` — эндпоинты управления пользователями и статистикой;
  * `pull_request_router.py` — эндпоинты для PR:

    * создание PR,
    * merge,
    * переназначение ревьюера.

Каждый роутер:

* принимает/возвращает **Pydantic-схемы** (`app/schemas`),

* через `Depends(...)` получает **сервис** (`TeamService`, `UserService`, `PullRequestService`),

* обрабатывает доменные исключения (`AlreadyExistsError`, `NotFoundError`, и т.д.) и мапит их в `HTTPException` с нужным статусом и JSON-ответом.

* `app/api/deps.py` — слой **dependency injection**:

  * даёт `AsyncSession` через `get_db`,
  * конструирует репозитории `TeamRepository`, `UserRepository`, `PullRequestRepository`,
  * конструирует сервисы `TeamService`, `UserService`, `PullRequestService`,
  * экспортирует удобные типы `TeamServiceDep`, `UserServiceDep`, `PullRequestServiceDep`.

---

## 2. Сервисный слой (бизнес-логика)

**Модули:**

* `app/services/team_service.py`
* `app/services/user_service.py`
* `app/services/pull_request_service.py`

**Ответственность:**

* Инкапсулирует бизнес-правила поверх репозиториев.
* Не знает про FastAPI и HTTP — работает только с моделями и схемами.
* Делает маппинг ORM-моделей (`app/models`) в Pydantic-схемы (`app/schemas`).

Примеры:

* `TeamService`

  * создаёт команду с участниками,
  * читает команду с участниками,
  * мапит `Team` + `User` → `TeamWithMembers`.

* `UserService`

  * меняет `is_active`,
  * отдаёт PR’ы, которые пользователь ревьюит,
  * строит статистику:

    * `ReviewStats.by_user` — сколько назначений на ревью по каждому пользователю,
    * `ReviewStats.by_pull_request` — сколько ревьюеров у каждого PR.

* `PullRequestService`

  * создание PR,
  * merge PR,
  * переназначение ревьюера (возвращает новый состав ревьюеров и ID, кем заменили).

---

## 3. Репозиторный слой (доступ к данным)

**Модули:**

* `app/repositories/team_repository.py`
* `app/repositories/user_repository.py`
* `app/repositories/pull_request_repository.py`

**Что делает:**

* Работает с `AsyncSession` и ORM-моделями (`app/models`).
* Инкапсулирует SQLAlchemy-запросы и транзакции.
* Отвечает за *инварианты данных* и бросает **доменные исключения**:

  * `AlreadyExistsError` — команда/PR уже существуют;
  * `NotFoundError` — нет пользователя/команды/PR;
  * `PullRequestMergedError` — попытка изменить merged PR;
  * `ReviewerNotAssignedError` — ревьюер не назначен на PR;
  * `NoReplacementCandidateError` — нет активного кандидата на замену и т.д.

---

## 4. Доменный слой (ORM-модели и Pydantic-схемы)

### ORM-модели (таблицы БД)

**Папка:** `app/models`

* `users.py` — `User`
* `teams.py` — `Team`
* `pull_requests.py` — `PullRequest`, `PRStatus`
* `pr_reviewers.py` — `PRReviewer` (таблица связи PR ↔ ревьюер)

Базовый класс: `app/core/db/base.py::Base`, который добавляет:

* `created_at`
* `updated_at`
* `to_dict()` для сериализации.

### Pydantic-схемы

**Папка:** `app/schemas`

* `team_shema.py` — `TeamMember`, `TeamWithMembers`, `TeamWithMembersGen`.
* `user_shema.py` — `UserFull`, `UserGen`, `SetIsActiveRequest`, `UserReviewPRs`,
  `UserReviewStat`, `ReviewStats`.
* `pull_request_shema.py` — `PullRequestShort`, `PullRequestFull`,
  `PullRequestCreatePayload`, `PullRequestMergePayload`,
  `PullRequestReassignPayload`, `PullRequestResponse`,
  `PullRequestReassignResponse`, `PRReviewStat`.

---

## 5. Инфраструктурный слой

**Папка:** `app/core`

* `config.py` — `Settings` на базе `pydantic-settings`:

  * подхватывает переменные из `.env`,
  * строит синхронный/асинхронный DSN для PostgreSQL,
  * задаёт `PROJECT_NAME`, `API_V1_STR`, настройки БД (основной и тестовой),
  * `SECRET_KEY` и прочие служебные параметры.

* `db/connect.py`:

  * создаёт `async_engine = create_async_engine(...)`,
  * `async_session = async_sessionmaker(...)`,
  * `get_db()` — `Depends`-функция, выдающая `AsyncSession` и откатывающая транзакцию при исключении.

* `db/base.py` — базовый ORM класс `Base`.

* `exceptions.py` — доменные исключения, которые используются во всём приложении.

---

## 6. Миграции и запуск

* **Миграции:** папка `migrations`, конфиг `alembic.ini`.

  * Структура БД поддерживается через Alembic (таблицы `users`, `teams`, `pull_requests`, `pr_reviewers`, enum `pr_status_enum`).

* **Docker / docker-compose:**

  * `docker-compose.yml` поднимает:

    * `db` (Postgres),
    * `migrate` (один раз гоняет `alembic upgrade head`),
    * `app` (uvicorn `app.main:app`).
  * `Dockerfile` собирает контейнер с Poetry, зависимостями и приложением.

---

## 7. Тесты

**Папка:** `tests`

* `test_healthcheck.py` — «заглушка»/smoke-тест.
* `tests/unit/repositories` — юнит-тесты репозиториев + `conftest.py` с фикстурами БД/сессии.
* `tests/unit/services` — юнит-тесты сервисов.

---

## 8. Типичный сценарий обработки запроса

На примере `POST /api/v1/pull-requests/add`:

1. **HTTP-запрос** попадает в `pull_request_router.py`.
2. FastAPI валидирует тело в `PullRequestCreatePayload`.
3. Через `Depends` создаётся:

   * `AsyncSession` → `PullRequestRepository` → `PullRequestService`.
4. `PullRequestService.create_pull_request()`:

   * вызывает `PullRequestRepository.create_pull_request(...)`,
   * репозиторий:

     * проверяет, что PR не существует,
     * находит команду автора,
     * выбирает до 2 активных ревьюеров,
     * создаёт `PullRequest` + `PRReviewer` записи.
5. Репозиторий возвращает ORM-модель `PullRequest`.
6. Сервис мапит её в `PullRequestFull`.
7. Роутер оборачивает в `PullRequestResponse` и отдаёт клиенту.
8. Если по пути кидается доменное исключение — роутер ловит его и возвращает соответствующий HTTP-код и JSON-ошибку.

