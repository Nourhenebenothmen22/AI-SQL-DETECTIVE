import json

import pytest
from httpx import AsyncClient

from app.core.config import Settings
from app.core.context import get_request_context
from app.modules.connections.registry import DEFAULT_CONNECTION_ID, ConnectionRegistry

MOCK_RO_DSN = "postgresql+psycopg://test_ro:mock_ro_token@mock-host:5432/test_db"
MOCK_APP_DSN = "postgresql+psycopg://test_app:mock_app_token@mock-host:5432/test_db"


def _make_settings(**overrides: object) -> Settings:
    defaults: dict[str, object] = {
        "app_env": "test",
        "database_ro_url": MOCK_RO_DSN,
        "database_app_url": MOCK_APP_DSN,
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def test_settings_provider_agnostic_llm_configuration() -> None:
    unconfigured = _make_settings(
        llm_provider="anthropic",
        llm_model="claude-3-5-sonnet",
        llm_api_key="",
    )
    assert unconfigured.llm_provider == "anthropic"
    assert unconfigured.is_llm_configured is False

    configured = _make_settings(
        llm_provider="google_genai",
        llm_model="gemini-2.5-flash",
        llm_api_key="mock-key",
    )
    assert configured.llm_provider == "google_genai"
    assert configured.is_llm_configured is True


def test_connection_registry_loads_default_and_extra_connections() -> None:
    extra = [
        {
            "id": "reporting_ro",
            "display_name": "Reporting Read Replica",
            "description": "Read-only reporting database",
            "dsn": "postgresql+psycopg://ro:mock_replica_token@replica:5432/reporting",
            "target_schemas": ["reporting"],
            "statement_timeout_ms": 4000,
            "max_rows": 5000,
        }
    ]
    settings = _make_settings(
        sql_hard_max_rows=1000,
        extra_connections_json=json.dumps(extra),
    )
    registry = ConnectionRegistry(settings)

    public_items = registry.list_public()
    assert len(public_items) == 2
    assert public_items[0].id == DEFAULT_CONNECTION_ID
    assert public_items[0].is_default is True
    assert public_items[1].id == "reporting_ro"
    assert public_items[1].max_rows == 1000  # Clamped to hard ceiling
    assert public_items[1].read_only is True


def test_connection_registry_rejects_duplicate_ids() -> None:
    extra = [
        {
            "id": DEFAULT_CONNECTION_ID,
            "display_name": "Duplicate",
            "dsn": "postgresql+psycopg://ro:mock_dup@host:5432/db",
            "target_schemas": ["ecommerce"],
        }
    ]
    settings = _make_settings(extra_connections_json=json.dumps(extra))
    with pytest.raises(ValueError, match="Duplicate database connection id"):
        ConnectionRegistry(settings)


def test_request_context_provides_default_local_actor() -> None:
    ctx = get_request_context()
    assert ctx.actor_id == "local-dev"
    assert "analyst" in ctx.roles


async def test_connections_endpoint_never_exposes_credentials(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/connections")
    assert response.status_code == 200

    body = response.json()
    raw_text = response.text
    assert body["default_connection_id"] == DEFAULT_CONNECTION_ID
    assert len(body["connections"]) == 1
    assert body["connections"][0]["read_only"] is True
    assert body["connections"][0]["target_schemas"] == ["ecommerce"]
    assert "mock_ro_secret" not in raw_text
    assert "db.internal" not in raw_text
    assert "dsn" not in body["connections"][0]


async def test_health_endpoint_reports_sanitized_status(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.v1.health._check_readonly_database", lambda _settings: "connected")

    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database_status"] == "connected"
    assert payload["llm_provider"] == "openai"
    assert payload["llm_configured"] is False
    assert "mock_ro_secret" not in response.text
