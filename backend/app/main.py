from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.modules.ai.service import DetectiveWorkflowService
from app.modules.connections.registry import ConnectionRegistry
from app.modules.evallaps import EvalLapsRepository, EvalLapsService
from app.modules.evals.service import EvalOpsService
from app.modules.execution.executor import SQLExecutor
from app.modules.history.repository import QueryRunRepository
from app.modules.scenarios.service import ScenarioGeneratorService
from app.modules.security.gate import SecurityGate


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    repo: QueryRunRepository | None = getattr(app.state, "query_run_repository", None)
    if repo is not None:
        repo.dispose()
    token_repo: EvalLapsRepository | None = getattr(app.state, "token_ledger_repository", None)
    if token_repo is not None:
        token_repo.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI modular monolith application.

    Use `uvicorn app.main:create_app --factory` so startup validates required
    environment variables immediately without import-time side effects.
    """
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        debug=resolved_settings.app_debug,
        lifespan=_lifespan,
    )

    # Wire runtime dependencies on app.state so create_app(settings=...) is
    # respected consistently and pools are disposed cleanly on shutdown.
    app.state.settings = resolved_settings
    app.state.connection_registry = ConnectionRegistry(resolved_settings)
    app.state.security_gate = SecurityGate()
    app.state.sql_executor = SQLExecutor()
    app.state.query_run_repository = QueryRunRepository(resolved_settings)
    app.state.token_ledger_repository = EvalLapsRepository(resolved_settings)
    app.state.evallaps_service = EvalLapsService(
        repository=app.state.token_ledger_repository,
        settings=resolved_settings,
    )
    app.state.workflow_service = DetectiveWorkflowService(
        settings=resolved_settings,
        security_gate=app.state.security_gate,
        sql_executor=app.state.sql_executor,
        history_repo=app.state.query_run_repository,
        token_ledger_repo=app.state.token_ledger_repository,
    )
    app.state.eval_service = EvalOpsService(
        settings=resolved_settings,
        gate=app.state.security_gate,
        executor=app.state.sql_executor,
        connections=app.state.connection_registry,
        workflow_service=app.state.workflow_service,
    )
    app.state.scenario_service = ScenarioGeneratorService(
        settings=resolved_settings,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    app.include_router(api_v1_router)
    return app
