from fastapi import Depends, Request

from app.core.config import Settings
from app.core.context import RequestContext, get_request_context
from app.modules.ai.service import DetectiveWorkflowService
from app.modules.connections.registry import ConnectionRegistry
from app.modules.evallaps import EvalLapsRepository, EvalLapsService
from app.modules.evals.service import EvalOpsService
from app.modules.execution.executor import SQLExecutor
from app.modules.history.repository import QueryRunRepository
from app.modules.scenarios.service import ScenarioGeneratorService
from app.modules.security.gate import SecurityGate


def get_app_settings(request: Request) -> Settings:
    """Provide validated application settings bound to the FastAPI app state."""
    return request.app.state.settings


def get_connection_registry(request: Request) -> ConnectionRegistry:
    """Provide the preconfigured backend-only connection registry."""
    return request.app.state.connection_registry


def get_security_gate(request: Request) -> SecurityGate:
    """Provide the deterministic SQLGlot Independent Security Gate."""
    return request.app.state.security_gate


def get_sql_executor(request: Request) -> SQLExecutor:
    """Provide the read-only PostgreSQL SQL executor."""
    return request.app.state.sql_executor


def get_query_run_repository(request: Request) -> QueryRunRepository:
    """Provide the app_meta query-run telemetry repository."""
    return request.app.state.query_run_repository


def get_workflow_service(request: Request) -> DetectiveWorkflowService:
    """Provide the 7-agent LangGraph AI SQL Detective workflow service."""
    return request.app.state.workflow_service


def get_eval_service(request: Request) -> EvalOpsService:
    """Provide the EvalOps benchmarking and golden test suite service."""
    return request.app.state.eval_service


def get_scenario_service(request: Request) -> ScenarioGeneratorService:
    """Provide the AI what-if scenario generator and sandbox service."""
    if not hasattr(request.app.state, "scenario_service"):
        request.app.state.scenario_service = ScenarioGeneratorService(
            settings=request.app.state.settings
        )
    return request.app.state.scenario_service


def get_token_ledger_repository(request: Request) -> EvalLapsRepository:
    """Provide the app_meta LLM token ledger repository."""
    if not hasattr(request.app.state, "token_ledger_repository"):
        request.app.state.token_ledger_repository = EvalLapsRepository(request.app.state.settings)
    return request.app.state.token_ledger_repository


def get_evallaps_service(request: Request) -> EvalLapsService:
    """Provide the EvalLaps LLMOps & FinOps observability service."""
    if not hasattr(request.app.state, "evallaps_service"):
        repo = get_token_ledger_repository(request)
        request.app.state.evallaps_service = EvalLapsService(
            repository=repo,
            settings=request.app.state.settings,
        )
    return request.app.state.evallaps_service


def get_current_context(
    context: RequestContext = Depends(get_request_context),
) -> RequestContext:
    """Provide request actor/role context (future auth boundary)."""
    return context
