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
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

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

    # Multi-Provider Resilient Failover Chain (100% Free Providers)
    llm_provider: str = Field(default="groq", min_length=1)
    llm_model: str = Field(default="qwen/qwen3.8-27b", min_length=1)
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    llm_timeout_seconds: int = Field(default=25, ge=5, le=120)

    # Dedicated Provider Credentials (supports single key or comma-separated multi-token pool)
    openai_api_key: SecretStr | None = None
    openai_api_keys: SecretStr | None = None
    openai_model: str = "gpt-4o-mini"

    google_api_key: SecretStr | None = None
    google_api_keys: SecretStr | None = None
    google_model: str = "gemini-2.0-flash"

    mistral_api_key: SecretStr | None = None
    mistral_api_keys: SecretStr | None = None
    mistral_model: str = "mistral-small-latest"

    openrouter_api_key: SecretStr | None = None
    openrouter_api_keys: SecretStr | None = None
    openrouter_model: str = "cognitivecomputations/dolphin3.0-r1-mistral-24b:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # High-Speed & Generous Providers (Groq, SambaNova, Cloudflare, Cohere, z.ai)
    groq_api_key: SecretStr | None = None
    groq_api_keys: SecretStr | None = None
    groq_model: str = "qwen/qwen3.8-27b"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    sambanova_api_key: SecretStr | None = None
    sambanova_api_keys: SecretStr | None = None
    sambanova_model: str = "gemma-4-31B-it"
    sambanova_base_url: str = "https://api.sambanova.ai/v1"

    cloudflare_api_key: SecretStr | None = None
    cloudflare_api_keys: SecretStr | None = None
    cloudflare_model: str = "@cf/meta/llama-3.3-70b-instruct"
    cloudflare_base_url: str | None = None

    cohere_api_key: SecretStr | None = None
    cohere_api_keys: SecretStr | None = None
    cohere_model: str = "command-r-plus"
    cohere_base_url: str = "https://api.cohere.com/v1"

    zai_api_key: SecretStr | None = None
    zai_api_keys: SecretStr | None = None
    zai_model: str = "glm-4-flash"
    zai_base_url: str | None = "https://open.bigmodel.cn/api/paas/v4/"

    kimi_api_key: SecretStr | None = None
    kimi_api_keys: SecretStr | None = None
    kimi_model: str = "moonshot-v1-8k"
    kimi_base_url: str = "https://api.moonshot.cn/v1"

    novita_api_key: SecretStr | None = None
    novita_api_keys: SecretStr | None = None
    novita_model: str = "meta-llama/llama-3.3-70b-instruct"
    novita_base_url: str = "https://api.novita.ai/v3/openai"

    meta_api_key: SecretStr | None = None
    meta_api_keys: SecretStr | None = None
    meta_model: str = "llama-3.3-70b-instruct"
    meta_base_url: str | None = None

    llm_fallback_chain: str = "groq,sambanova,openrouter,google,cohere,cloudflare,zai,meta"

    # Optional LangSmith Observability
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "ai-sql-detective"

    @field_validator(
        "llm_api_key",
        "llm_base_url",
        "openai_api_key",
        "openai_api_keys",
        "google_api_key",
        "google_api_keys",
        "mistral_api_key",
        "mistral_api_keys",
        "openrouter_api_key",
        "openrouter_api_keys",
        "openrouter_base_url",
        "groq_api_key",
        "groq_api_keys",
        "sambanova_api_key",
        "sambanova_api_keys",
        "cloudflare_api_key",
        "cloudflare_api_keys",
        "cloudflare_base_url",
        "cohere_api_key",
        "cohere_api_keys",
        "cohere_base_url",
        "zai_api_key",
        "zai_api_keys",
        "zai_base_url",
        "kimi_api_key",
        "kimi_api_keys",
        "kimi_base_url",
        "novita_api_key",
        "novita_api_keys",
        "novita_base_url",
        "meta_api_key",
        "meta_api_keys",
        "meta_base_url",
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

    def get_provider_keys(self, provider_name: str) -> list[SecretStr]:
        """Return all configured, unique non-empty SecretStr keys for a provider."""
        p = provider_name.strip().lower()
        if p in ("google_genai", "gemini"):
            p = "google"
        elif p == "mistralai":
            p = "mistral"

        raw_keys: list[str] = []

        # 1. Multi-token pool (e.g. GROQ_API_KEYS="k1,k2,k3")
        multi_field = getattr(self, f"{p}_api_keys", None)
        if multi_field and multi_field.get_secret_value().strip():
            for item in multi_field.get_secret_value().split(","):
                val = item.strip()
                if val and val not in raw_keys:
                    raw_keys.append(val)

        # 2. Single-token field (e.g. GROQ_API_KEY="k1")
        single_field = getattr(self, f"{p}_api_key", None)
        if single_field and single_field.get_secret_value().strip():
            val = single_field.get_secret_value().strip()
            if val and val not in raw_keys:
                raw_keys.append(val)

        # 3. Generic fallback from settings.llm_api_key
        if not raw_keys and self.llm_provider.lower() == p and self.llm_api_key:
            val = self.llm_api_key.get_secret_value().strip()
            if val and val not in raw_keys:
                raw_keys.append(val)

        return [SecretStr(k) for k in raw_keys]

    @property
    def configured_llm_providers(self) -> list[str]:
        known = [
            "groq",
            "sambanova",
            "openrouter",
            "google",
            "cohere",
            "cloudflare",
            "zai",
            "meta",
            "kimi",
            "novita",
            "mistral",
            "openai",
        ]
        configured: list[str] = []
        for p in known:
            if self.get_provider_keys(p):
                configured.append(p)

        # Fallback generic provider if not caught above
        if not configured and self.llm_api_key and self.llm_api_key.get_secret_value().strip():
            configured.append(self.llm_provider)

        return configured

    @property
    def total_llm_tokens_armed(self) -> int:
        """Total number of unique API keys armed across all configured providers."""
        return sum(len(self.get_provider_keys(p)) for p in self.configured_llm_providers)

    @property
    def is_llm_configured(self) -> bool:
        return len(self.configured_llm_providers) > 0

    @property
    def is_multi_provider_resilient(self) -> bool:
        return self.total_llm_tokens_armed > 1

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
