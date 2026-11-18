from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, START, StateGraph

from app.modules.ai.nodes import DetectiveNodes
from app.modules.ai.state import DetectiveState
from app.modules.connections.registry import DatabaseConnectionSpec
from app.modules.execution.executor import SQLExecutor
from app.modules.security.gate import SecurityGate


def _route_after_review(state: DetectiveState) -> str:
    if state.get("review_status") == "needs_revision" and state.get("revision_feedback"):
        return "sql_generator"
    return "security_gate"


def _route_after_security_gate(state: DetectiveState) -> str:
    if state.get("security_status") == "passed" and state.get("validated_sql_artifact") is not None:
        return "sql_executor"
    return END


def _route_after_execution(state: DetectiveState) -> str | list[str]:
    status = state.get("execution_status")
    if status == "error" and state.get("stages") and state["stages"][-1]["status"] == "retrying":
        return "sql_generator"
    if status != "success":
        return END
    if state.get("explain_plan"):
        # Parallel fan-out: Result Explainer + Optimization Agent run concurrently.
        return ["result_explainer", "optimization_agent"]
    return "result_explainer"


def build_detective_graph(
    *,
    llm: BaseChatModel,
    security_gate: SecurityGate,
    sql_executor: SQLExecutor,
    connection_spec: DatabaseConnectionSpec,
    hard_max_rows: int,
    lock_timeout_ms: int,
    llm_timeout_seconds: int,
) -> Any:
    """Compile the 7-agent AI SQL Detective LangGraph StateGraph."""
    nodes = DetectiveNodes(
        llm=llm,
        security_gate=security_gate,
        sql_executor=sql_executor,
        connection_spec=connection_spec,
        hard_max_rows=hard_max_rows,
        lock_timeout_ms=lock_timeout_ms,
        llm_timeout_seconds=llm_timeout_seconds,
    )

    builder: StateGraph[DetectiveState] = StateGraph(DetectiveState)
    builder.add_node("schema_analyst", nodes.schema_analyst)
    builder.add_node("sql_generator", nodes.sql_generator)
    builder.add_node("query_reviewer", nodes.query_reviewer)
    builder.add_node("security_gate", nodes.security_gate)
    builder.add_node("sql_executor", nodes.sql_executor)
    builder.add_node("result_explainer", nodes.result_explainer)
    builder.add_node("optimization_agent", nodes.optimization_agent)

    builder.add_edge(START, "schema_analyst")
    builder.add_edge("schema_analyst", "sql_generator")
    builder.add_edge("sql_generator", "query_reviewer")

    builder.add_conditional_edges(
        "query_reviewer",
        _route_after_review,
        {
            "sql_generator": "sql_generator",
            "security_gate": "security_gate",
        },
    )
    builder.add_conditional_edges(
        "security_gate",
        _route_after_security_gate,
        {
            "sql_executor": "sql_executor",
            END: END,
        },
    )
    builder.add_conditional_edges(
        "sql_executor",
        _route_after_execution,
        {
            "sql_generator": "sql_generator",
            "result_explainer": "result_explainer",
            "optimization_agent": "optimization_agent",
            END: END,
        },
    )

    builder.add_edge("result_explainer", END)
    builder.add_edge("optimization_agent", END)

    return builder.compile()
