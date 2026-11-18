from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class ConfigurationError(RuntimeError):
    """Raised when required environment configuration is missing or invalid.

    Error messages intentionally omit secret input values so credentials are
    never leaked to logs, tracebacks, or terminal output.
    """


class Settings(BaseSettings):
    """Centralized, environment-backed application configuration."""

    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AI SQL Detective"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "production"] = "development"
    app_debug: bool = False
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # Required Database DSNs (loaded exclusively from environment / root .env)
    database_ro_url: SecretStr = Field(
        ...,
        description="Dedicated read-only PostgreSQL DSN for the ecommerce target schema.",
    )
    database_app_url: SecretStr = Field(
        ...,
        description="Scoped PostgreSQL DSN for app_meta query-run telemetry.",
    )
    database_migrator_url: SecretStr | None = Field(
        default=None,
        description="Migration/seeding DSN used exclusively by Alembic and seed CLI.",
    )
    extra_connections_json: str = Field(
        default="[]",
        description="Optional JSON array of additional backend-configured read-only connections.",
    )

    # Query Execution & Security Guardrails
    sql_default_max_rows: int = Field(default=200, ge=1, le=1000)
    sql_hard_max_rows: int = Field(default=1000, ge=1, le=5000)
    sql_statement_timeout_ms: int = Field(default=5000, ge=500, le=30000)
    sql_lock_timeout_ms: int = Field(default=1000, ge=100, le=10000)
    workflow_timeout_seconds: int = Field(default=60, ge=5, le=300)

    # Provider-Agnostic LLM Configuration (LangChain)
    llm_provider: str = Field(default="openai", min_length=1)
    llm_model: str = Field(default="gpt-4o-mini", min_length=1)
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    llm_timeout_seconds: int = Field(default=25, ge=5, le=120)

    # Optional LangSmith Observability
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "ai-sql-detective"

    @field_validator(
        "llm_api_key",
        "llm_base_url",
        "langsmith_api_key",
        "database_migrator_url",
        mode="before",
    )
    @classmethod
    def _empty_str_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("database_ro_url", "database_app_url", "database_migrator_url")
    @classmethod
    def _validate_postgres_dsn(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        raw = value.get_secret_value().strip()
        if not raw or not raw.startswith(("postgresql://", "postgresql+psycopg://")):
            raise ValueError(
                "Must be a valid PostgreSQL DSN starting with 'postgresql://' "
                "or 'postgresql+psycopg://'."
            )
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_llm_configured(self) -> bool:
        return self.llm_api_key is not None and bool(self.llm_api_key.get_secret_value().strip())

    @property
    def effective_default_max_rows(self) -> int:
        return min(self.sql_default_max_rows, self.sql_hard_max_rows)


def to_psycopg_dsn(sqlalchemy_dsn: str) -> str:
    """Convert a SQLAlchemy PostgreSQL+Psycopg DSN to a native Psycopg 3 DSN."""
    return sqlalchemy_dsn.replace("postgresql+psycopg://", "postgresql://", 1)


def load_settings(*, env_file: Path | str | None = ROOT_ENV_FILE) -> Settings:
    """Load and validate application settings without exposing secret values on error."""
    try:
        return Settings(_env_file=env_file)
    except ValidationError as exc:
        issues: list[str] = []
        for err in exc.errors():
            field_path = ".".join(str(part) for part in err.get("loc", ()))
            env_name = field_path.upper() if field_path else "UNKNOWN"
            err_type = err.get("type", "invalid")
            if err_type == "missing":
                issues.append(f"{env_name}: required environment variable is missing")
            else:
                issues.append(f"{env_name}: invalid configuration ({err.get('msg', err_type)})")
        summary = "; ".join(issues)
        raise ConfigurationError(
            f"Application configuration validation failed: {summary}. "
            "Check your root .env file or environment variables (see .env.example)."
        ) from None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached, startup-validated application settings."""
    return load_settings()
