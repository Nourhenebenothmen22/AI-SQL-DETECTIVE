from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.modules.ai.state import TokenLedgerRecord
from app.modules.evallaps import (
    GPT4O_INPUT_COST_PER_TOKEN,
    GPT4O_OUTPUT_COST_PER_TOKEN,
    PROVIDER_RENEWAL_REGISTRY,
    EvalLapsRepository,
    EvalLapsService,
    calculate_savings_usd,
    get_provider_renewal_meta,
)
from app.schemas.evallaps import (
    EvalLapsSummary,
)


def test_finops_gpt4o_pricing_constants() -> None:
    """Verify standard commercial baseline pricing: $2.50 / 1M prompt, $10.00 / 1M completion."""
    assert pytest.approx(0.0000025) == GPT4O_INPUT_COST_PER_TOKEN
    assert pytest.approx(0.0000100) == GPT4O_OUTPUT_COST_PER_TOKEN


def test_calculate_savings_usd_zero_tokens() -> None:
    """Verify zero token usage yields $0.00 savings."""
    assert calculate_savings_usd(0, 0) == 0.0


def test_calculate_savings_usd_realistic_workload() -> None:
    """Verify accurate monetary savings computation against GPT-4o pricing."""
    prompt_tokens = 1_000
    completion_tokens = 500
    # Expected: (1000 * 2.50e-6) + (500 * 10.00e-6) = 0.0025 + 0.0050 = 0.0075 USD
    expected = (1_000 * 0.0000025) + (500 * 0.000010)
    savings = calculate_savings_usd(prompt_tokens, completion_tokens)
    assert savings == pytest.approx(expected, abs=1e-6)
    assert savings == 0.0075


def test_provider_renewal_registry_all_ten_free_providers() -> None:
    """Verify all 10 free-tier providers have detailed renewal diagnostic specifications."""
    expected_providers = [
        "groq",
        "sambanova",
        "google",
        "cloudflare",
        "openrouter",
        "cohere",
        "zai",
        "meta",
        "kimi",
        "novita",
    ]
    for p in expected_providers:
        msg = f"Provider {p} missing from PROVIDER_RENEWAL_REGISTRY"
        assert p in PROVIDER_RENEWAL_REGISTRY, msg
        meta = get_provider_renewal_meta(p)
        assert meta.provider_name == p
        assert len(meta.display_name) > 0
        assert len(meta.renewal_window_label) > 0
        assert len(meta.free_tier_limits_label) > 0
        assert len(meta.description) > 0
        assert meta.renewal_type in (
            "sliding_window_1m",
            "rolling_daily_24h",
            "monthly_credits",
            "quota_static_tier",
        )


def test_provider_renewal_characteristics() -> None:
    """Verify specific renewal window types and auto-renewable statuses."""
    groq = get_provider_renewal_meta("groq")
    assert groq.renewal_type == "sliding_window_1m"
    assert groq.is_auto_renewable is True

    google = get_provider_renewal_meta("google")
    assert google.renewal_type == "rolling_daily_24h"
    assert google.is_auto_renewable is True

    cohere = get_provider_renewal_meta("cohere")
    assert cohere.renewal_type == "monthly_credits"
    assert cohere.is_auto_renewable is True

    zai = get_provider_renewal_meta("zai")
    assert zai.renewal_type == "quota_static_tier"
    assert zai.is_auto_renewable is False

    unknown = get_provider_renewal_meta("unregistered_provider_xyz")
    assert unknown.renewal_type == "quota_static_tier"
    assert unknown.is_auto_renewable is False


def test_evallaps_repository_empty_summary_fallback() -> None:
    """Verify EvalLapsRepository handles connection errors safely returning empty summary."""
    mock_settings = Settings(
        _env_file=None,
        app_env="test",
        database_ro_url="postgresql+psycopg://sql_detective_ro:mock@localhost:5432/testdb",
        database_app_url="postgresql+psycopg://sql_detective_app:mock@localhost:5432/testdb",
        llm_provider="groq",
    )
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = Exception("DB connection refused")

    repo = EvalLapsRepository(mock_settings, engine=mock_engine)
    summary = repo.get_summary(window_days=7)
    assert isinstance(summary, EvalLapsSummary)
    assert summary.total_tokens == 0
    assert summary.total_savings_usd == 0.0
    assert summary.total_calls == 0


def test_evallaps_repository_record_entries_db_fallback() -> None:
    """Verify record_entries returns 0 safely if database write fails."""
    mock_settings = Settings(
        _env_file=None,
        app_env="test",
        database_ro_url="postgresql+psycopg://sql_detective_ro:mock@localhost:5432/testdb",
        database_app_url="postgresql+psycopg://sql_detective_app:mock@localhost:5432/testdb",
        llm_provider="groq",
    )
    mock_engine = MagicMock()
    mock_engine.begin.side_effect = Exception("Write failed")

    repo = EvalLapsRepository(mock_settings, engine=mock_engine)
    sample_entry: TokenLedgerRecord = {
        "stage_id": "schema_analyst",
        "provider_name": "groq",
        "model_name": "qwen/qwen3.8-27b",
        "key_fingerprint": "33HA",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "estimated_savings_usd": 0.00075,
        "real_cost_usd": 0.0,
        "http_status": 200,
        "latency_ms": 120.5,
    }
    count = repo.record_entries(run_id=uuid4(), entries=[sample_entry])
    assert count == 0


def test_evallaps_service_orchestration() -> None:
    """Verify EvalLapsService correctly coordinates diagnostics and repository calls."""
    mock_repo = MagicMock(spec=EvalLapsRepository)
    mock_repo.get_summary.return_value = EvalLapsSummary(
        total_tokens=1500,
        prompt_tokens=1000,
        completion_tokens=500,
        total_savings_usd=0.0075,
        total_calls=3,
        today_tokens=1500,
        today_savings_usd=0.0075,
        providers_count=1,
        top_provider="groq",
    )
    mock_repo.record_entries.return_value = 2

    mock_settings = Settings(
        _env_file=None,
        app_env="test",
        database_ro_url="postgresql+psycopg://sql_detective_ro:mock@localhost:5432/testdb",
        database_app_url="postgresql+psycopg://sql_detective_app:mock@localhost:5432/testdb",
        llm_provider="groq",
    )
    service = EvalLapsService(repository=mock_repo, settings=mock_settings)

    # 1. Test summary
    summary = service.get_observability_summary(window_days=30)
    assert summary.total_tokens == 1500
    assert summary.total_savings_usd == 0.0075
    assert summary.top_provider == "groq"
    mock_repo.get_summary.assert_called_once_with(window_days=30)

    # 2. Test record
    run_id = uuid4()
    count = service.record_run_telemetry(run_id=run_id, entries=[])
    assert count == 2
    mock_repo.record_entries.assert_called_once_with(run_id, [])

    # 3. Test renewal diagnostics
    diagnostics = service.get_renewal_diagnostics()
    assert len(diagnostics) == len(PROVIDER_RENEWAL_REGISTRY)
    names = {d.provider_name for d in diagnostics}
    assert "groq" in names
    assert "google" in names
    assert "sambanova" in names
