from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_name: str = "Finanzas por Voz API"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://app:change-me@localhost:5432/finanzas"
    database_host: str | None = None
    database_port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = "postgres"
    database_user: str | None = None
    database_password: SecretStr | None = None
    jwt_secret: str = Field(default="development-only-secret-change-me", min_length=32)
    access_token_minutes: int = Field(default=15, ge=5, le=60)
    refresh_token_days: int = Field(default=30, ge=1, le=90)
    login_max_failures: int = Field(default=5, ge=3, le=20)
    login_block_minutes: int = Field(default=15, ge=1, le=120)
    cors_origins: list[AnyHttpUrl] = [AnyHttpUrl("http://localhost:8081")]
    public_app_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8081")
    email_delivery_mode: Literal["file", "smtp"] = "file"
    email_from: str = "no-reply@finanzas.local"
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    inbound_email_domain: str = "inbound.finanzas.local"
    inbound_email_secret: str = Field(
        default="development-inbound-email-secret-change-me",
        min_length=32,
    )
    inbound_email_enabled: bool = False
    privacy_mode: Literal["strict", "standard"] = "strict"
    financial_ai_enabled: bool = False
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5-mini"

    @property
    def alembic_database_url(self) -> str:
        """Escape percent signs consumed by Alembic's ConfigParser interpolation."""
        return self.database_url.replace("%", "%%")

    @field_validator("database_url", mode="before")
    @classmethod
    def select_psycopg_driver(cls, value: str) -> str:
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value

    @model_validator(mode="after")
    def validate_deployed_environment(self) -> "Settings":
        separate_database_values = {
            "DATABASE_HOST": self.database_host,
            "DATABASE_USER": self.database_user,
            "DATABASE_PASSWORD": self.database_password,
        }
        if any(value is not None for value in separate_database_values.values()):
            missing = [
                name for name, value in separate_database_values.items() if value is None
            ]
            if missing:
                raise ValueError(f"Missing database environment variables: {', '.join(missing)}")
            assert self.database_host is not None
            assert self.database_user is not None
            assert self.database_password is not None
            self.database_url = URL.create(
                drivername="postgresql+psycopg",
                username=self.database_user,
                password=self.database_password.get_secret_value(),
                host=self.database_host,
                port=self.database_port,
                database=self.database_name,
                query={"sslmode": "require"},
            ).render_as_string(hide_password=False)

        if self.app_env not in {"staging", "production"}:
            return self
        if "change-me" in self.database_url:
            raise ValueError("Deployed environments require a real database credential")
        if self.jwt_secret == "development-only-secret-change-me" or "change-me" in self.jwt_secret:
            raise ValueError("Deployed environments require a unique JWT secret")
        if any(origin.host in {"localhost", "127.0.0.1"} for origin in self.cors_origins):
            raise ValueError("Deployed environments cannot allow localhost CORS origins")
        if self.email_delivery_mode == "smtp" and not self.smtp_host:
            raise ValueError("SMTP delivery requires an SMTP host")
        if self.public_app_url.host in {"localhost", "127.0.0.1"}:
            raise ValueError("Deployed environments require a public application URL")
        if "change-me" in self.inbound_email_secret:
            raise ValueError("Deployed environments require an inbound email secret")
        if self.privacy_mode == "strict" and self.financial_ai_enabled:
            raise ValueError("Strict privacy mode does not allow external financial AI")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
