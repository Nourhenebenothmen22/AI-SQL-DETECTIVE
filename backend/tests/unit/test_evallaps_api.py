from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.modules.evallaps import PROVIDER_RENEWAL_REGISTRY


@pytest.mark.asyncio
async def test_get_evallaps_summary_endpoint(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/evallaps/summary returns 200 and valid FinOps summary."""
    response = await async_client.get("/api/v1/evallaps/summary?window_days=14")
    assert response.status_code == 200
    data = response.json()

    assert "total_tokens" in data
    assert "prompt_tokens" in data
    assert "completion_tokens" in data
    assert "total_savings_usd" in data
    assert "total_calls" in data
    assert "today_tokens" in data
    assert "this_month_tokens" in data
    assert isinstance(data["total_tokens"], int)
    assert isinstance(data["total_savings_usd"], float)


@pytest.mark.asyncio
async def test_get_evallaps_providers_endpoint(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/evallaps/providers returns 200 and provider breakdown."""
    response = await async_client.get("/api/v1/evallaps/providers?window_days=30")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_evallaps_stages_endpoint(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/evallaps/stages returns 200 and agent stage breakdown."""
    response = await async_client.get("/api/v1/evallaps/stages?window_days=30")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_evallaps_run_ledger_endpoint(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/evallaps/runs/{run_id} returns 200 and token items list."""
    test_run_id = str(uuid4())
    response = await async_client.get(f"/api/v1/evallaps/runs/{test_run_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_evallaps_renewals_catalog_endpoint(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/evallaps/renewals returns the full 10 free provider catalog."""
    response = await async_client.get("/api/v1/evallaps/renewals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(PROVIDER_RENEWAL_REGISTRY)

    provider_names = {item["provider_name"] for item in data}
    assert "groq" in provider_names
    assert "sambanova" in provider_names
    assert "google" in provider_names
    assert "openrouter" in provider_names
    assert "cloudflare" in provider_names
    assert "cohere" in provider_names
    assert "zai" in provider_names
    assert "meta" in provider_names
    assert "kimi" in provider_names
    assert "novita" in provider_names

    groq_meta = next(item for item in data if item["provider_name"] == "groq")
    assert groq_meta["renewal_type"] == "sliding_window_1m"
    assert groq_meta["is_auto_renewable"] is True
