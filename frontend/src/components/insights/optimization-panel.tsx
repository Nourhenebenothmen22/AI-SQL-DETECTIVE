"use client";

import { Check, Copy, Gauge, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDurationMs, formatNumber } from "@/lib/format";
import type { OptimizationRecommendationResponse, PlanSummaryResponse } from "@/types/api";

export interface ParallelOptimizationState {
  status: "idle" | "running" | "completed" | "partial" | "skipped";
  durationMs: number | null;
}

interface OptimizationPanelProps {
  optimizationState: ParallelOptimizationState;
  recommendations: OptimizationRecommendationResponse[];
  planSummary: PlanSummaryResponse | null;
  explainPlan: Record<string, unknown>[] | Record<string, unknown> | null;
}

export function OptimizationPanel({
  optimizationState,
  recommendations,
  planSummary,
  explainPlan,
}: OptimizationPanelProps) {
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [showRawPlan, setShowRawPlan] = useState(false);

  const handleCopySnippet = async (snippet: string, idx: number) => {
    await navigator.clipboard.writeText(snippet);
    setCopiedIdx(idx);
    window.setTimeout(() => setCopiedIdx(null), 1500);
  };

  return (
    <div className="space-y-4">
      {/* Separate Parallel Optimization Agent Status Header */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-border-subtle bg-card px-4 py-3">
        <div className="flex items-center gap-2.5">
          {optimizationState.status === "running" ? (
            <Loader2 className="h-4 w-4 animate-spin text-accent-secondary" aria-hidden="true" />
          ) : (
            <Gauge className="h-4 w-4 text-accent-secondary" aria-hidden="true" />
          )}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-primary">
              Optimization Agent · EXPLAIN (FORMAT JSON)
            </h3>
            <p className="text-[11px] text-text-secondary">
              Runs in parallel with Result Explainer without blocking query delivery. Advisory only
              (never auto-applied; never uses EXPLAIN ANALYZE).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-xs tabular-nums">
          {optimizationState.status === "running" ? (
            <Badge variant="cyan">Running in parallel</Badge>
          ) : optimizationState.status === "completed" ? (
            <Badge variant="success">
              Completed
              {optimizationState.durationMs !== null
                ? ` · ${formatDurationMs(optimizationState.durationMs)}`
                : ""}
            </Badge>
          ) : optimizationState.status === "partial" ? (
            <Badge variant="warning">Deterministic Plan Fallback</Badge>
          ) : optimizationState.status === "skipped" ? (
            <Badge variant="default">Skipped</Badge>
          ) : (
            <Badge variant="default">Idle</Badge>
          )}
        </div>
      </div>

      {/* Plan Metrics Summary */}
      {planSummary ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-border-subtle bg-card p-3">
            <p className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">
              Root Plan Node
            </p>
            <p className="mt-1 font-mono text-sm font-semibold text-text-primary">
              {planSummary.root_node_type}
            </p>
          </div>
          <div className="rounded-lg border border-border-subtle bg-card p-3">
            <p className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">
              Estimated Total Cost
            </p>
            <p className="mt-1 font-mono text-sm font-semibold tabular-nums text-accent-secondary">
              {planSummary.total_cost.toFixed(2)}
            </p>
          </div>
          <div className="rounded-lg border border-border-subtle bg-card p-3">
            <p className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">
              Estimated Rows
            </p>
            <p className="mt-1 font-mono text-sm font-semibold tabular-nums text-text-primary">
              {formatNumber(planSummary.estimated_rows)}
            </p>
          </div>
          <div className="rounded-lg border border-border-subtle bg-card p-3">
            <p className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">
              Plan Operators
            </p>
            <p className="mt-1 truncate font-mono text-xs text-text-primary">
              {planSummary.node_types.join(", ")}
            </p>
          </div>
        </div>
      ) : null}

      {/* Recommendation Cards */}
      {recommendations.length > 0 ? (
        <div className="space-y-3">
          {recommendations.map((rec, idx) => (
            <article
              key={`${rec.title}-${idx}`}
              className="rounded-lg border border-border-subtle bg-card p-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      rec.severity === "high"
                        ? "error"
                        : rec.severity === "warning"
                          ? "warning"
                          : "cyan"
                    }
                  >
                    {rec.severity.toUpperCase()}
                  </Badge>
                  <Badge variant="default">{rec.category}</Badge>
                  <h4 className="text-sm font-semibold text-text-primary">{rec.title}</h4>
                </div>
              </div>

              <p className="mt-2 text-xs leading-relaxed text-text-secondary">{rec.detail}</p>
              <p className="mt-2 text-xs leading-relaxed text-text-primary">{rec.suggestion}</p>

              {rec.suggested_sql_or_index ? (
                <div className="mt-3 rounded-md border border-border-subtle bg-canvas p-3">
                  <div className="mb-1.5 flex items-center justify-between">
                    <span className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">
                      Advisory Recommendation (Not Auto-Executed)
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => void handleCopySnippet(rec.suggested_sql_or_index ?? "", idx)}
                    >
                      {copiedIdx === idx ? (
                        <Check className="h-3 w-3 text-status-success" aria-hidden="true" />
                      ) : (
                        <Copy className="h-3 w-3" aria-hidden="true" />
                      )}
                      <span>{copiedIdx === idx ? "Copied" : "Copy"}</span>
                    </Button>
                  </div>
                  <pre className="overflow-x-auto font-mono text-xs text-accent-secondary">
                    <code>{rec.suggested_sql_or_index}</code>
                  </pre>
                </div>
              ) : null}
            </article>
          ))}
        </div>
      ) : optimizationState.status === "running" ? (
        <div className="rounded-lg border border-border-subtle bg-card p-6 text-center text-xs text-text-secondary">
          Analyzing PostgreSQL EXPLAIN (FORMAT JSON) plan in parallel...
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border-subtle bg-card px-6 py-10 text-center">
          <Sparkles className="h-6 w-6 text-text-secondary/60" aria-hidden="true" />
          <p className="mt-2.5 text-sm font-medium text-text-primary">
            {planSummary
              ? "Query plan looks efficient"
              : "No EXPLAIN (FORMAT JSON) plan inspected yet"}
          </p>
          <p className="mt-1 max-w-md text-xs text-text-secondary">
            {planSummary
              ? "No high-cost sequential scans or major bottlenecks were flagged in this plan."
              : "Execute a validated query to inspect its PostgreSQL query plan and optimization advice."}
          </p>
        </div>
      )}

      {explainPlan ? (
        <div className="rounded-lg border border-border-subtle bg-card p-3.5">
          <div className="flex items-center justify-between">
            <span className="font-mono text-xs font-medium text-text-primary">
              Raw EXPLAIN (FORMAT JSON)
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowRawPlan((prev) => !prev)}
              aria-expanded={showRawPlan}
            >
              {showRawPlan ? "Hide JSON" : "Inspect JSON"}
            </Button>
          </div>
          {showRawPlan ? (
            <pre className="mt-3 max-h-72 overflow-auto rounded-md border border-border-subtle bg-canvas p-3 font-mono text-[11px] text-text-secondary">
              <code>{JSON.stringify(explainPlan, null, 2)}</code>
            </pre>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
