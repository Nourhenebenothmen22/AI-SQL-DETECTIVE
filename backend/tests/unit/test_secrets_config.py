import logging
import re
from pathlib import Path

import pytest

from app.core.config import ConfigurationError, Settings, load_settings
from app.core.logging import SecretRedactingFilter, redact_sensitive_text
from app.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_missing_required_env_vars_fail_clearly_without_leaking_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DATABASE_RO_URL", raising=False)
    monkeypatch.delenv("DATABASE_APP_URL", raising=False)

    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(env_file=None)

    message = str(exc_info.value)
    assert "DATABASE_RO_URL" in message
    assert "DATABASE_APP_URL" in message


def test_invalid_secret_dsn_error_never_echoes_secret_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_sentinel = "ULTRA_SENSITIVE_LEAK_CHECK_99182"
    monkeypatch.setenv("DATABASE_RO_URL", f"mysql://admin:{secret_sentinel}@host/db")
    monkeypatch.setenv("DATABASE_APP_URL", "postgresql+psycopg://app:ok@host:5432/db")

    with pytest.raises(ConfigurationError) as exc_info:
        load_settings(env_file=None)

    message = str(exc_info.value)
    assert "DATABASE_RO_URL" in message
    assert secret_sentinel not in message


def test_settings_repr_redacts_all_secret_fields() -> None:
    ro_secret = "SECRET_RO_TOKEN_ABC"
    app_secret = "SECRET_APP_TOKEN_XYZ"
    llm_secret = "SECRET_LLM_KEY_123"
    settings = Settings(
        _env_file=None,
        database_ro_url=f"postgresql+psycopg://ro:{ro_secret}@host:5432/db",
        database_app_url=f"postgresql+psycopg://app:{app_secret}@host:5432/db",
        llm_api_key=llm_secret,
    )

    rendered = f"{settings!r} {settings!s}"
    assert ro_secret not in rendered
    assert app_secret not in rendered
    assert llm_secret not in rendered


def test_gitignore_protects_env_and_secret_files() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    lines = {line.strip() for line in gitignore.splitlines()}
    assert ".env" in lines
    assert ".env.*" in lines
    assert "!.env.example" in lines
    assert "*.pem" in lines
    assert "*.key" in lines


def test_repository_contains_no_unsafe_next_public_secrets_or_hardcoded_credentials() -> None:
    unsafe_next_public = re.compile(
        r"NEXT_PUBLIC_[A-Z0-9_]*(SECRET|PASSWORD|TOKEN|API_KEY|PRIVATE|DATABASE|DSN|CREDENTIAL)"
    )
    forbidden_patterns = [
        re.compile(r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
        re.compile(
            r"dev_readonly_password|dev_app_password|dev_migrator_password|dev_postgres_admin"
        ),
        re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{20,}"),
    ]

    scan_targets: list[Path] = [
        REPO_ROOT / "docker-compose.yml",
        REPO_ROOT / ".env.example",
        REPO_ROOT / "docker" / "postgres" / "init" / "01_init_roles.sh",
    ]
    for directory in (
        REPO_ROOT / "backend" / "app",
        REPO_ROOT / "frontend" / "src",
        REPO_ROOT / ".github",
    ):
        if directory.exists():
            scan_targets.extend(p for p in directory.rglob("*") if p.is_file())

    violations: list[str] = []
    for path in scan_targets:
        content = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(REPO_ROOT)
        if unsafe_next_public.search(content):
            violations.append(f"{rel}: unsafe NEXT_PUBLIC_ secret variable detected")
        for pattern in forbidden_patterns:
            if pattern.search(content):
                violations.append(
                    f"{rel}: forbidden credential/key pattern matched ({pattern.pattern})"
                )

    assert not violations, f"Secret hygiene violations found: {violations}"


def test_log_redacting_filter_masks_dsn_passwords_bearer_tokens_and_api_keys() -> None:
    raw = (
        "Failed connecting postgresql+psycopg://ro:my_secret_pw@db:5432/app "
        "with Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.token and key sk-proj-1234567890abcdef1234"
    )
    redacted = redact_sensitive_text(raw)
    assert "my_secret_pw" not in redacted
    assert "eyJhbGciOiJIUzI1NiJ9.token" not in redacted
    assert "sk-proj-1234567890abcdef1234" not in redacted
    assert "postgresql+psycopg://ro:***@db:5432/app" in redacted

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="DSN=%s",
        args=("postgresql://user:hidden_pass_99@host:5432/db",),
        exc_info=None,
    )
    assert SecretRedactingFilter().filter(record) is True
    assert "hidden_pass_99" not in record.getMessage()


def test_create_app_binds_custom_settings_to_app_state() -> None:
    custom = Settings(
        _env_file=None,
        app_env="test",
        database_ro_url="postgresql+psycopg://ro:mock1@custom-host:5432/customdb",
        database_app_url="postgresql+psycopg://app:mock2@custom-host:5432/customdb",
        llm_provider="anthropic",
    )
    app = create_app(settings=custom)
    try:
        assert app.state.settings is custom
        assert app.state.connection_registry.get().dsn.get_secret_value() == (
            custom.database_ro_url.get_secret_value()
        )
    finally:
        app.state.query_run_repository.dispose()
