# Архитектура БД

## Общие моменты

Все модели наследуются от `Base`, в котором уже определены служебные поля:

* `created_at` — `TIMESTAMP WITH TIME ZONE`, `server_default=now()`
* `updated_at` — `TIMESTAMP WITH TIME ZONE`, `server_default=now()`, `onupdate=now()`

То есть **каждая таблица** в БД имеет:

* `created_at`
* `updated_at`

---

## Таблица `teams`

Модель: `Team` (`app/models/teams.py`)

**Назначение:** команда разработчиков.

**Поля:**

* `name: str` — PK
  `mapped_column(primary_key=True)`

* `created_at`, `updated_at` — от `Base`

**Связи:**

* `users: list[User]` — `relationship(back_populates="team", cascade="all, delete-orphan")`
  Логически: **1 команда — N пользователей**.

---

## Таблица `users`

Модель: `User` (`app/models/users.py`)

**Назначение:** пользователь/разработчик.

**Поля:**

* `id: str` — PK
  `mapped_column(primary_key=True)` — строковый идентификатор пользователя (например, логин/ID из внешней системы).

* `username: str` — имя пользователя
  `String(100), nullable=False`

* `is_active: bool` — активен ли пользователь
  `Boolean, default=True, nullable=False`

* `team_name: str | None` — FK на команду
  `ForeignKey("teams.name", ondelete="SET NULL"), nullable=True`
  Пользователь может быть без команды (NULL).

* `created_at`, `updated_at` — от `Base`

**Связи:**

* `team: Team` — `relationship(back_populates="users")`
  **Многие пользователи принадлежат одной команде**.

* `authored_prs: list[PullRequest]` — PR’ы, где пользователь автор
  `relationship(back_populates="author", foreign_keys="PullRequest.author_id")`

* `reviewing_prs: list[PRReviewer]` — связи как ревьюер
  `relationship(back_populates="reviewer", cascade="all, delete-orphan")`

---

## Таблица `pull_requests`

Модель: `PullRequest` + enum `PRStatus` (`app/models/pull_requests.py`)

**Enum:**

```python
class PRStatus(str, Enum):
    OPEN = "OPEN"
    MERGED = "MERGED"
```

В БД это `SAEnum(PRStatus, name="pr_status_enum")`.

**Назначение:** pull request.

**Поля:**

* `id: str` — PK
  Идентификатор PR (строка, например, из Git).

* `title: str` — заголовок PR
  `String`, `nullable=False` (см. миграции)

* `author_id: str` — автор PR
  `ForeignKey("users.id", ondelete="CASCADE"), nullable=False`

* `status: PRStatus` — статус PR
  `Enum('OPEN', 'MERGED')`, `default=OPEN`, `nullable=False`

* `merged_at: datetime | None` — время merge PR (если он в статусе MERGED)

* `created_at`, `updated_at` — от `Base`

**Связи:**

* `author: User` — `relationship(back_populates="authored_prs")`
  **Один пользователь может быть автором многих PR**.

* `reviewers: list[PRReviewer]` — `relationship(back_populates="pr", cascade="all, delete-orphan")`
  Связи через таблицу `pr_reviewers` (см. ниже).

---

## Таблица `pr_reviewers`

Модель: `PRReviewer` (`app/models/pr_reviewers.py`)

**Назначение:** связь PR ↔ ревьюер (многие-ко-многим между `PullRequest` и `User`).

**Поля:**

* `id: int` — PK, `autoincrement=True`

* `pr_id: str` — FK на PR
  `ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False`

* `reviewer_id: str` — FK на пользователя
  `ForeignKey("users.id", ondelete="CASCADE"), nullable=False`

* `created_at`, `updated_at` — от `Base`

**Уникальность:**

```python
__table_args__ = (
    UniqueConstraint("pr_id", "reviewer_id", name="uq_pr_reviewer"),
)
```

Один и тот же пользователь **не может быть назначен ревьюером на один PR дважды**.

**Связи:**

* `pr: PullRequest` — `relationship(back_populates="reviewers")`

* `reviewer: User` — `relationship(back_populates="reviewing_prs")`
