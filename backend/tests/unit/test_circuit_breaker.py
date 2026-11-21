import time
from typing import Any

import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.modules.ai.llm import (
    LLMCircuitBreaker,
    build_chat_model,
    is_circuit_breaker_error,
)
from app.modules.ai.nodes import DetectiveNodes
from app.modules.ai.schemas import SchemaAnalysisOutput, SQLGenerationOutput
from app.modules.ai.state import DetectiveState
from app.modules.connections.registry import DatabaseConnectionSpec


class DummyRateLimitError(Exception):
    status_code = 429


class DummyAuthError(Exception):
    status_code = 401


def test_is_circuit_breaker_error_detection() -> None:
    assert is_circuit_breaker_error(DummyRateLimitError("Rate limit exceeded")) is True
    assert is_circuit_breaker_error(DummyAuthError("Unauthorized key")) is True
    assert (
        is_circuit_breaker_error(Exception("Error code: 429 - You have no credits remaining"))
        is True
    )
    assert is_circuit_breaker_error(Exception("401 Invalid Authentication token")) is True
    assert is_circuit_breaker_error(Exception("402 - A payment method is required")) is True
    assert (
        is_circuit_breaker_error(Exception("ResourceExhausted: Quota exceeded for model")) is True
    )
    assert is_circuit_breaker_error(ValueError("Syntax error in query")) is False
    assert is_circuit_breaker_error(RuntimeError("Database connection lost")) is False


def test_circuit_breaker_quarantine_lifecycle() -> None:
    cb = LLMCircuitBreaker(default_ttl_seconds=10.0)
    provider = "openai"

    assert cb.is_quarantined(provider) is False
    assert cb.get_quarantined_providers() == []

    # Record failure
    cb.record_failure(provider, "HTTP 429 - Quota exhausted")
    assert cb.is_quarantined(provider) is True
    assert cb.get_quarantined_providers() == ["openai"]

    # Manual clear
    cb.clear(provider)
    assert cb.is_quarantined(provider) is False
    assert cb.get_quarantined_providers() == []

    # Short TTL expiry check
    cb.record_failure(provider, "HTTP 401 - Expired token", ttl_seconds=0.01)
    time.sleep(0.02)
    assert cb.is_quarantined(provider) is False


def test_build_chat_model_promotes_healthy_when_primary_quarantined(
    test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    cb = LLMCircuitBreaker(default_ttl_seconds=300.0)
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_ro_url=test_settings.database_ro_url,
        database_app_url=test_settings.database_app_url,
        openai_api_key="sk-test-openai",
        google_api_key="AIzaSy-test-google",
        llm_fallback_chain="openai,google",
    )

    class _DummyModel:
        def __init__(self, name: str) -> None:
            self.name = name

        def with_fallbacks(self, fallbacks: list[Any]) -> Any:
            return {"primary": self.name, "fallbacks": [f.name for f in fallbacks]}

    monkeypatch.setattr(
        "app.modules.ai.llm.init_chat_model",
        lambda model, model_provider, **_kw: _DummyModel(f"{model_provider}:{model}"),
    )

    # 1. Normal order when neither is quarantined
    normal_model = build_chat_model(settings, circuit_breaker=cb)
    assert isinstance(normal_model, dict)
    assert normal_model["primary"] == "openai:gpt-4o-mini"
    assert normal_model["fallbacks"] == ["google_genai:gemini-2.0-flash"]

    # 2. When OpenAI is quarantined, Google is promoted to primary
    cb.record_failure("openai", "HTTP 429 Quota exhausted")
    reordered_model = build_chat_model(settings, circuit_breaker=cb)
    assert isinstance(reordered_model, dict)
    assert reordered_model["primary"] == "google_genai:gemini-2.0-flash"
    assert reordered_model["fallbacks"] == ["openai:gpt-4o-mini"]


@pytest.mark.asyncio
async def test_detective_nodes_dynamically_bypasses_quarantined_provider() -> None:
    cb = LLMCircuitBreaker(default_ttl_seconds=300.0)
    invoked_providers: list[str] = []

    class MockModel:
        def __init__(self, name: str, should_fail: bool) -> None:
            self.name = name
            self.should_fail = should_fail

        def with_structured_output(self, schema: Any, **_kwargs: Any) -> Any:
            model_name = self.name
            should_fail = self.should_fail

            class _FakeRunnable:
                async def ainvoke(self, _messages: Any, **_kw: Any) -> Any:
                    invoked_providers.append(model_name)
                    if should_fail:
                        cb.record_failure(model_name, "HTTP 429 Quota Exceeded")
                        raise DummyRateLimitError("429 Quota")
                    if schema == SchemaAnalysisOutput:
                        return SchemaAnalysisOutput(
                            selected_tables=["ecommerce.customers"],
                            relevant_columns=["id"],
                            join_paths=[],
                            metric_definitions=[],
                            ambiguities=[],
                            needs_clarification=False,
                            query_intent="lookup",
                            query_complexity="simple",
                            recommended_strategy="simple select",
                        )
                    if schema == SQLGenerationOutput:
                        return SQLGenerationOutput(
                            sql="SELECT id FROM ecommerce.customers LIMIT 10",
                            rationale="Selected customers",
                            assumptions=[],
                        )
                    return None

            return _FakeRunnable()

    def mock_factory(settings: Any) -> Any:
        # Prioritize healthy models via cb
        models = [
            ("openai", MockModel("openai", should_fail=True)),
            ("google", MockModel("google", should_fail=False)),
        ]
        healthy = [m for name, m in models if not cb.is_quarantined(name)]
        quarantined = [m for name, m in models if cb.is_quarantined(name)]
        chain = healthy + quarantined
        primary = chain[0]

        class _FallbackChain:
            def with_structured_output(self, schema: Any, **kwargs: Any) -> Any:
                primary_so = primary.with_structured_output(schema, **kwargs)
                fb_so = chain[1].with_structured_output(schema, **kwargs)

                class _ChainWrapper:
                    async def ainvoke(self, messages: Any, **kw: Any) -> Any:
                        try:
                            return await primary_so.ainvoke(messages, **kw)
                        except Exception:
                            return await fb_so.ainvoke(messages, **kw)

                return _ChainWrapper()

        return _FallbackChain()

    dummy_spec = DatabaseConnectionSpec(
        id="demo",
        display_name="Demo",
        description="",
        dsn=SecretStr("postgresql+psycopg://user:pw@host:5432/db"),
        target_schemas=("ecommerce",),
        read_only=True,
        max_rows=100,
        statement_timeout_ms=5000,
    )

    nodes = DetectiveNodes(
        llm=mock_factory(None),
        security_gate=None,  # type: ignore[arg-type]
        sql_executor=None,  # type: ignore[arg-type]
        connection_spec=dummy_spec,
        hard_max_rows=200,
        lock_timeout_ms=1000,
        llm_timeout_seconds=5,
        settings=object(),
        llm_factory=mock_factory,
    )

    state: DetectiveState = {
        "user_question": "List customers",
        "schema_prompt": "ecommerce.customers",
        "allowed_schemas": ["ecommerce"],
        "revision_count": 0,
        "execution_retry_count": 0,
    }

    # Step 1: Run schema_analyst node
    # OpenAI fails, records 429, falls back to Google
    res1 = await nodes.schema_analyst(state, config={})
    assert res1["selected_tables"] == ["ecommerce.customers"]
    assert invoked_providers == ["openai", "google"]
    assert cb.is_quarantined("openai") is True

    # Step 2: Run sql_generator node
    # OpenAI is already quarantined! It should be bypassed immediately, calling ONLY Google!
    invoked_providers.clear()
    state["selected_tables"] = res1["selected_tables"]
    res2 = await nodes.sql_generator(state, config={})
    assert res2["candidate_sql"] == "SELECT id FROM ecommerce.customers LIMIT 10"
    assert invoked_providers == ["google"]  # OpenAI was NOT called!


def test_multi_token_pool_rotation_and_quarantine(
    test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure multiple keys under the same provider rotate and quarantine independently."""
    cb = LLMCircuitBreaker(default_ttl_seconds=300.0)
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_ro_url=test_settings.database_ro_url,
        database_app_url=test_settings.database_app_url,
        groq_api_keys="gsk_token_alpha_1111,gsk_token_beta_2222",
        sambanova_api_keys="samba_key_3333",
        llm_fallback_chain="groq,sambanova",
    )

    assert settings.total_llm_tokens_armed == 3
    assert len(settings.get_provider_keys("groq")) == 2
    assert len(settings.get_provider_keys("sambanova")) == 1

    class _DummyKeyModel:
        def __init__(self, key_id: str) -> None:
            self.key_id = key_id

        def with_fallbacks(self, fallbacks: list[Any]) -> Any:
            return {"primary": self.key_id, "fallbacks": [f.key_id for f in fallbacks]}

    # Intercept init_chat_model to record key_id passed via callback
    monkeypatch.setattr(
        "app.modules.ai.llm.init_chat_model",
        lambda model, model_provider, **kw: _DummyKeyModel(
            kw["callbacks"][0].provider if kw.get("callbacks") else f"{model_provider}:{model}"
        ),
    )

    # 1. Initially, groq:1111 is primary, followed by groq:2222 and sambanova:3333
    chain = build_chat_model(settings, circuit_breaker=cb)
    assert isinstance(chain, dict)
    assert chain["primary"] == "groq:1111"
    assert chain["fallbacks"] == ["groq:2222", "sambanova:3333"]

    # 2. When groq:1111 hits 429 quota exhaustion, only that key is quarantined!
    cb.record_failure("groq:1111", "HTTP 429 Quota Exceeded")
    assert cb.is_quarantined("groq:1111") is True
    assert cb.is_quarantined("groq:2222") is False

    # 3. Next build_chat_model immediately promotes healthy groq:2222 as primary!
    chain2 = build_chat_model(settings, circuit_breaker=cb)
    assert isinstance(chain2, dict)
    assert chain2["primary"] == "groq:2222"
    assert chain2["fallbacks"] == ["sambanova:3333", "groq:1111"]
