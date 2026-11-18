from dataclasses import dataclass
from typing import Any

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


@dataclass(frozen=True, slots=True)
class SequentialScanInfo:
    relation_name: str
    estimated_rows: int
    total_cost: float
    filter_expression: str | None


@dataclass(frozen=True, slots=True)
class PlanFinding:
    """Deterministic optimization observation derived from EXPLAIN (FORMAT JSON)."""

    severity: str  # "info" | "warning" | "high"
    category: str
    title: str
    detail: str
    suggestion: str


@dataclass(frozen=True, slots=True)
class PlanSummary:
    """Structured metrics and deterministic observations extracted from an EXPLAIN JSON plan."""

    root_node_type: str
    startup_cost: float
    total_cost: float
    estimated_rows: int
    plan_width: int
    node_types: tuple[str, ...]
    sequential_scans: tuple[SequentialScanInfo, ...]
    has_sort: bool
    has_nested_loop: bool
    has_hash_join: bool
    findings: tuple[PlanFinding, ...]


def _walk_plan_nodes(node: dict[str, Any], acc: list[dict[str, Any]]) -> None:
    acc.append(node)
    for child in node.get("Plans") or ():
        if isinstance(child, dict):
            _walk_plan_nodes(child, acc)


def _detect_select_star_from_sql(sql: str) -> bool:
    if not sql.strip():
        return False
    try:
        parsed = sqlglot.parse_one(sql, read="postgres")
    except ParseError:
        return False
    return any(
        isinstance(star.parent, (exp.Select, exp.Column)) for star in parsed.find_all(exp.Star)
    )


def analyze_explain_plan(
    explain_json: list[dict[str, Any]] | dict[str, Any] | None,
    *,
    sql: str = "",
    has_select_star: bool | None = None,
) -> PlanSummary | None:
    """Parse PostgreSQL EXPLAIN (FORMAT JSON) output into structured metrics and findings."""
    if not explain_json:
        return None

    top_entry: dict[str, Any] | None = None
    if isinstance(explain_json, list) and explain_json and isinstance(explain_json[0], dict):
        top_entry = explain_json[0]
    elif isinstance(explain_json, dict):
        top_entry = explain_json

    if top_entry is None:
        return None

    root_plan = top_entry.get("Plan")
    if not isinstance(root_plan, dict):
        return None

    all_nodes: list[dict[str, Any]] = []
    _walk_plan_nodes(root_plan, all_nodes)

    node_types: list[str] = []
    seq_scans: list[SequentialScanInfo] = []
    has_sort = False
    has_nested_loop = False
    has_hash_join = False

    for node in all_nodes:
        node_type = str(node.get("Node Type", "Unknown"))
        if node_type not in node_types:
            node_types.append(node_type)

        if node_type == "Seq Scan":
            seq_scans.append(
                SequentialScanInfo(
                    relation_name=str(node.get("Relation Name", "unknown")),
                    estimated_rows=int(node.get("Plan Rows", 0) or 0),
                    total_cost=float(node.get("Total Cost", 0.0) or 0.0),
                    filter_expression=(
                        str(node["Filter"]) if node.get("Filter") is not None else None
                    ),
                )
            )
        elif node_type == "Sort":
            has_sort = True
        elif node_type == "Nested Loop":
            has_nested_loop = True
        elif node_type == "Hash Join":
            has_hash_join = True

    findings: list[PlanFinding] = []
    for scan in seq_scans:
        if scan.filter_expression and scan.total_cost >= 100.0:
            severity = "high" if scan.total_cost >= 400.0 else "warning"
            findings.append(
                PlanFinding(
                    severity=severity,
                    category="indexing",
                    title=f"Filtered sequential scan on '{scan.relation_name}'",
                    detail=(
                        f"PostgreSQL estimates a full sequential scan (cost {scan.total_cost:.1f}, "
                        f"~{scan.estimated_rows} rows) with filter {scan.filter_expression}."
                    ),
                    suggestion=(
                        f"Evaluate adding a targeted B-tree or composite index on "
                        f"'{scan.relation_name}' covering the filter columns."
                    ),
                )
            )
        elif scan.estimated_rows >= 5000 and scan.total_cost >= 150.0:
            findings.append(
                PlanFinding(
                    severity="info",
                    category="scan",
                    title=f"Large sequential scan on '{scan.relation_name}'",
                    detail=(
                        f"Sequential scan estimates {scan.estimated_rows} rows "
                        f"(cost {scan.total_cost:.1f})."
                    ),
                    suggestion=(
                        "Add selective WHERE predicates or pre-aggregate if full-table scan "
                        "is unnecessary."
                    ),
                )
            )

    root_cost = float(root_plan.get("Total Cost", 0.0) or 0.0)
    if has_sort and root_cost >= 300.0:
        findings.append(
            PlanFinding(
                severity="warning",
                category="sorting",
                title="Explicit sort on high-cost query plan",
                detail=f"Plan includes a Sort node contributing to total cost {root_cost:.1f}.",
                suggestion=(
                    "Consider an index aligned with the ORDER BY / GROUP BY columns to enable "
                    "ordered index scans."
                ),
            )
        )

    wildcard_projection = (
        has_select_star if has_select_star is not None else _detect_select_star_from_sql(sql)
    )
    if wildcard_projection:
        findings.append(
            PlanFinding(
                severity="info",
                category="projection",
                title="Wildcard column projection (SELECT *)",
                detail="Fetching all columns increases row width and prevents index-only scans.",
                suggestion="Project only the required columns explicitly.",
            )
        )

    return PlanSummary(
        root_node_type=str(root_plan.get("Node Type", "Unknown")),
        startup_cost=float(root_plan.get("Startup Cost", 0.0) or 0.0),
        total_cost=root_cost,
        estimated_rows=int(root_plan.get("Plan Rows", 0) or 0),
        plan_width=int(root_plan.get("Plan Width", 0) or 0),
        node_types=tuple(node_types),
        sequential_scans=tuple(seq_scans),
        has_sort=has_sort,
        has_nested_loop=has_nested_loop,
        has_hash_join=has_hash_join,
        findings=tuple(findings),
    )
