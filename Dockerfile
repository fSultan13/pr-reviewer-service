# Stage 1: deps (Poetry + venv с зависимостями)
FROM python:3.12-slim AS deps

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VERSION=2.2.1 \
    POETRY_CACHE_DIR="/tmp/poetry_cache" \
    POETRY_VIRTUALENVS_IN_PROJECT=1

ENV PATH="${POETRY_HOME}/bin:${PATH}"

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    gettext \
 && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -
RUN poetry --version

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --no-ansi --no-cache

# Stage 2: production runtime
FROM python:3.12-bookworm AS production

WORKDIR /app

# Копируем виртуалку из deps
COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:${PATH}"

# Кладём исходники
COPY . .

EXPOSE 8080

RUN addgroup --system app && adduser --system --group app && chown -R app:app /app
RUN mkdir /mnt/logs/ && chown app:app /mnt/logs/

USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
