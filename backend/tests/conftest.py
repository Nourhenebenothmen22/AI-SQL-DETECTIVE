from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app
from app.modules.ai.service import DetectiveWorkflowService
from app.modules.history.repository import QueryRunRecordInput


class FakeQueryRunRepository:
    def __init__(self) -> None:
        self.records: list[QueryRunRecordInput] = []

    def record_run(self, record: QueryRunRecordInput) -> UUID:
        self.records.append(record)
        return uuid4()

    def dispose(self) -> None:
        return None


class FakeEvalLapsRepository:
    def __init__(self) -> None:
        self.recorded_entries: list[tuple[UUID | None, list[Any]]] = []

    def record_entries(self, run_id: UUID | None, entries: list[Any]) -> int:
        self.recorded_entries.append((run_id, entries))
        return len(entries)

    def dispose(self) -> None:
        return None


@pytest.fixture
def fake_history_repo() -> FakeQueryRunRepository:
    return FakeQueryRunRepository()


@pytest.fixture
def fake_token_ledger_repo() -> FakeEvalLapsRepository:
    return FakeEvalLapsRepository()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        database_ro_url="postgresql+psycopg://sql_detective_ro:mock_ro_secret@db.internal:5432/testdb",
        database_app_url="postgresql+psycopg://sql_detective_app:mock_app_secret@db.internal:5432/testdb",
        llm_provider="groq",
        llm_model="qwen/qwen3.8-27b",
        llm_api_key=None,
    )


@pytest.fixture
async def async_client(
    test_settings: Settings,
    fake_history_repo: FakeQueryRunRepository,
    fake_token_ledger_repo: FakeEvalLapsRepository,
) -> AsyncClient:
    app = create_app(settings=test_settings)
    app.state.query_run_repository.dispose()
    app.state.token_ledger_repository.dispose()
    app.state.query_run_repository = fake_history_repo
    app.state.token_ledger_repository = fake_token_ledger_repo
    app.state.workflow_service = DetectiveWorkflowService(
        settings=test_settings,
        security_gate=app.state.security_gate,
        sql_executor=app.state.sql_executor,
        history_repo=fake_history_repo,
        token_ledger_repo=fake_token_ledger_repo,
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
