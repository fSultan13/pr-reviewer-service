import logging
import secrets

from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL
from typing_extensions import Self

logger = logging.getLogger("app")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = ""
    SECRET_KEY: str = secrets.token_urlsafe(32)

    BACKEND_HOST: str = "localhost"
    BACKEND_PORT: int = 8080

    PROJECT_NAME: str

    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    POSTGRES_SERVER_TEST: str
    POSTGRES_PORT_TEST: int = 5432
    POSTGRES_USER_TEST: str
    POSTGRES_PASSWORD_TEST: str = ""
    POSTGRES_DB_TEST: str = ""

    @computed_field
    @property
    def get_async_database_uri(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    @computed_field
    def get_back_http_url(self) -> str:
        return f"http://{self.BACKEND_HOST}:{self.BACKEND_PORT}"

    @computed_field
    @property
    def get_async_database_test_uri(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.POSTGRES_USER_TEST,
            password=self.POSTGRES_PASSWORD_TEST,
            host=self.POSTGRES_SERVER_TEST,
            port=self.POSTGRES_PORT_TEST,
            database=self.POSTGRES_DB_TEST,
        )

    @computed_field
    @property
    def get_database_uri(self) -> URL:
        return URL.create(
            drivername="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        )

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "none":
            message = (
                f'The value of {var_name} is "none", '
                "for security, please change it, at least for deployments."
            )
            logger.warning(message, stacklevel=1)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)

        return self


settings = Settings()
