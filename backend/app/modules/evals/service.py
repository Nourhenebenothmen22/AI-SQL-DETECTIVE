import logging
import uuid
from datetime import UTC, datetime

from app.core.config import Settings
from app.core.context import RequestContext
from app.modules.ai.service import DetectiveWorkflowService
from app.modules.connections.registry import ConnectionRegistry, DatabaseConnectionSpec
from app.modules.evals.evaluator import evaluate_test_case
from app.modules.evals.golden_dataset import GOLDEN_BENCHMARK_CASES
from app.modules.execution.executor import SQLExecutor
from app.modules.security.gate import SecurityGate
from app.schemas.evals import (
    CategoryMetric,
    DifficultyMetric,
    EvalCaseResult,
    EvalRunRequest,
    EvalRunResponse,
    EvalRunSummary,
    GoldenTestCase,
)

logger = logging.getLogger(__name__)


class EvalOpsService:
    """Manages the Golden Benchmark suite, evaluation runs, and multi-model metrics."""

    def __init__(
        self,
        *,
        settings: Settings,
        gate: SecurityGate,
        executor: SQLExecutor,
        connections: ConnectionRegistry,
        workflow_service: DetectiveWorkflowService,
    ) -> None:
        self._settings = settings
        self._gate = gate
        self._executor = executor
        self._connections = connections
        self._workflow = workflow_service
        self._history: list[EvalRunResponse] = []

    def get_cases(self, difficulty: str | None = None) -> list[GoldenTestCase]:
        """Return the golden benchmark test cases, optionally filtered by difficulty."""
        if not difficulty:
            return GOLDEN_BENCHMARK_CASES
        return [c for c in GOLDEN_BENCHMARK_CASES if c.difficulty == difficulty]

    def get_latest_run(self) -> EvalRunResponse | None:
        """Return the most recent benchmark run results."""
        if not self._history:
            self._initialize_default_run()
        return self._history[-1] if self._history else None

    def get_history(self) -> list[EvalRunSummary]:
        """Return historical summary KPIs across benchmark executions."""
        if not self._history:
            self._initialize_default_run()
        return [run.summary for run in reversed(self._history)]

    def _initialize_default_run(self) -> None:
        """Seed a clean baseline benchmark run so UI renders immediately on first load."""
        if self._settings.app_env == "test":
            return
        try:
            spec = self._connections.get("ecommerce_demo")
        except KeyError:
            return

        results: list[EvalCaseResult] = []
        for case in GOLDEN_BENCHMARK_CASES:
            res = evaluate_test_case(
                case=case,
                candidate_sql=case.golden_sql,
                spec=spec,
                gate=self._gate,
                executor=self._executor,
            )
            results.append(res)

        summary = self._compute_summary(
            run_id=f"bench_baseline_{uuid.uuid4().hex[:8]}",
            model_name=f"{self._settings.llm_provider}:{self._settings.llm_model} (Baseline)",
            results=results,
        )
        self._history.append(EvalRunResponse(summary=summary, results=results))

    def _compute_summary(
        self,
        *,
        run_id: str,
        model_name: str,
        results: list[EvalCaseResult],
    ) -> EvalRunSummary:
        total = len(results)
        passed = sum(1 for r in results if r.execution_accuracy)
        vast = sum(1 for r in results if r.vast_passed)
        avg_latency = (sum(r.latency_ms for r in results) / total) if total > 0 else 0.0

        # Group by difficulty
        diff_stats: dict[str, list[bool]] = {}
        cat_stats: dict[str, list[bool]] = {}
        for r in results:
            diff_stats.setdefault(r.difficulty, []).append(r.execution_accuracy)
            cat_stats.setdefault(r.category, []).append(r.execution_accuracy)

        by_difficulty = {
            diff: DifficultyMetric(
                total=len(vals),
                passed=sum(1 for v in vals if v),
                accuracy_percentage=round((sum(1 for v in vals if v) / len(vals)) * 100, 1),
            )
            for diff, vals in diff_stats.items()
        }

        by_category = {
            cat: CategoryMetric(
                total=len(vals),
                passed=sum(1 for v in vals if v),
                accuracy_percentage=round((sum(1 for v in vals if v) / len(vals)) * 100, 1),
            )
            for cat, vals in cat_stats.items()
        }

        return EvalRunSummary(
            run_id=run_id,
            model_name=model_name,
            timestamp=datetime.now(UTC),
            total_cases=total,
            passed_cases=passed,
            vast_passed_count=vast,
            accuracy_percentage=round((passed / total) * 100, 1) if total > 0 else 0.0,
            vast_percentage=round((vast / total) * 100, 1) if total > 0 else 0.0,
            avg_latency_ms=round(avg_latency, 2),
            by_difficulty=by_difficulty,
            by_category=by_category,
        )

    async def run_benchmark(
        self,
        request: EvalRunRequest,
        spec: DatabaseConnectionSpec,
        context: RequestContext,
    ) -> EvalRunResponse:
        """Execute the benchmark suite against candidate queries or LangGraph pipeline."""
        cases = GOLDEN_BENCHMARK_CASES
        if request.case_ids:
            allowed = set(request.case_ids)
            cases = [c for c in cases if c.id in allowed]
        elif request.difficulty:
            cases = [c for c in cases if c.difficulty == request.difficulty]

        results: list[EvalCaseResult] = []
        model_label = f"{self._settings.llm_provider}:{self._settings.llm_model}"

        for case in cases:
            candidate_sql: str | None = None
            if request.mock_run:
                # Mock run uses canonical golden queries
                candidate_sql = case.golden_sql
            else:
                try:
                    # Run LangGraph NL-to-SQL generation workflow
                    wf_res = await self._workflow.run_workflow(
                        question=case.question,
                        spec=spec,
                        context=context,
                        max_rows=100,
                        include_explain=False,
                    )
                    candidate_sql = wf_res.validated_sql or wf_res.candidate_sql
                except Exception as exc:
                    logger.warning("Error running workflow for case %s: %s", case.id, exc)
                    candidate_sql = None

            case_result = evaluate_test_case(
                case=case,
                candidate_sql=candidate_sql,
                spec=spec,
                gate=self._gate,
                executor=self._executor,
            )
            results.append(case_result)

        run_id = f"bench_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        display_model = f"{model_label} (Ground Truth Mock)" if request.mock_run else model_label
        summary = self._compute_summary(
            run_id=run_id,
            model_name=display_model,
            results=results,
        )

        response = EvalRunResponse(summary=summary, results=results)
        self._history.append(response)
        return response
