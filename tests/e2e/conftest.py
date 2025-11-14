from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.config import settings

BASE_URL = settings.get_back_http_url


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture
async def client(base_url: str):
    async with AsyncClient(base_url=base_url, timeout=5.0) as c:
        yield c


@pytest.fixture
def unique_suffix() -> str:
    return uuid4().hex[:8]
