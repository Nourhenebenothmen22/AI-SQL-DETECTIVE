"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Award,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Code2,
  Copy,
  Cpu,
  Database,
  FlaskConical,
  Loader2,
  Play,
  RotateCw,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { formatDurationMs, formatNumber } from "@/lib/format";
import type { EvalCaseResult, EvalRunRequest } from "@/types/api";

export default function EvalsPage() {
  const queryClient = useQueryClient();
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>("all");
  const [expandedCaseId, setExpandedCaseId] = useState<string | null>(null);
  const [copiedSqlKey, setCopiedSqlKey] = useState<string | null>(null);

  // Fetch the latest evaluation run
  const { data: latestRun, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["evals", "latest"],
    queryFn: ({ signal }) => apiClient.getLatestEvalRun(signal),
    refetchOnWindowFocus: false,
  });

  // Mutation to trigger benchmark runs
  const runMutation = useMutation({
    mutationFn: (payload: EvalRunRequest) => apiClient.runBenchmark(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(["evals", "latest"], data);
      void queryClient.invalidateQueries({ queryKey: ["evals", "history"] });
    },
  });

  const handleCopy = async (key: string, text: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedSqlKey(key);
    window.setTimeout(() => setCopiedSqlKey(null), 1500);
  };

  const summary = latestRun?.summary;
  const results = latestRun?.results ?? [];

  const filteredResults = results.filter((res) => {
    if (selectedDifficulty === "all") return true;
    return res.difficulty === selectedDifficulty;
  });

  const isRunning = runMutation.isPending;

  return (
    <div className="space-y-6 p-4 md:p-6 lg:p-8">
      {/* Header with Title, Model Badge and Action Buttons */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-text-primary">
              AI Model Evaluation &amp; EvalOps Benchmark
            </h1>
            <Badge variant="indigo">
              <FlaskConical className="h-3 w-3" aria-hidden="true" />
              EvalOps v1.0
            </Badge>
          </div>
          <p className="mt-1 text-xs leading-relaxed text-text-secondary">
            Continuous regression testing, schema grounding, and Execution Accuracy (EX) scored
            against 10 canonical golden queries on live PostgreSQL 16.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={isRunning}
            onClick={() => runMutation.mutate({ mock_run: true })}
            className="text-xs"
          >
            <Zap className="h-3.5 w-3.5 text-accent-secondary" aria-hidden="true" />
            <span>Fast Baseline</span>
          </Button>

          <Button
            variant="primary"
            size="sm"
            disabled={isRunning}
            onClick={() => runMutation.mutate({ mock_run: false })}
            className="text-xs"
          >
            {isRunning ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
            ) : (
              <Play className="h-3.5 w-3.5" aria-hidden="true" />
            )}
            <span>{isRunning ? "Evaluating Model..." : "Run Live Benchmark"}</span>
          </Button>
        </div>
      </header>

      {/* Model Metadata Banner */}
      {summary ? (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border-subtle bg-surface px-4 py-2.5">
          <div className="flex items-center gap-2 text-xs font-medium text-text-primary">
            <Cpu className="h-4 w-4 text-accent-primary" aria-hidden="true" />
            <span>Evaluated Model:</span>
            <span className="font-mono text-accent-secondary">{summary.model_name}</span>
          </div>
          <div className="flex items-center gap-3 font-mono text-[11px] tabular-nums text-text-secondary">
            <span>Run ID: {summary.run_id}</span>
            <span>·</span>
            <span>{new Date(summary.timestamp).toLocaleTimeString()}</span>
          </div>
        </div>
      ) : null}

      {/* Error state */}
      {isError ? (
        <div className="rounded-lg border border-status-error/40 bg-status-error/10 p-4 text-xs text-status-error">
          <p className="font-semibold">Unable to load benchmark results</p>
          <p className="mt-1 text-text-secondary">
            {error instanceof Error ? error.message : "Error contacting benchmark service."}
          </p>
          <Button variant="outline" size="sm" onClick={() => void refetch()} className="mt-3">
            <RotateCw className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Retry</span>
          </Button>
        </div>
      ) : null}

      {/* Top 4 KPI Metrics Grid */}
      {summary ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* 1. Execution Accuracy (EX) */}
          <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-xs">
            <div className="flex items-center justify-between text-text-secondary">
              <span className="text-[11px] font-medium uppercase tracking-wider">
                Execution Accuracy (EX)
              </span>
              <Award className="h-4 w-4 text-status-success" aria-hidden="true" />
            </div>
            <p className="mt-2 font-mono text-2xl font-bold tabular-nums text-status-success">
              {summary.accuracy_percentage.toFixed(1)}%
            </p>
            <p className="mt-1 text-[11px] text-text-secondary">
              {summary.passed_cases} of {summary.total_cases} queries produced exact result sets.
            </p>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface">
              <div
                className="h-full bg-status-success transition-all duration-300"
                style={{ width: `${Math.min(100, summary.accuracy_percentage)}%` }}
              />
            </div>
          </div>

          {/* 2. Deterministic AST Validity (VAST) */}
          <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-xs">
            <div className="flex items-center justify-between text-text-secondary">
              <span className="text-[11px] font-medium uppercase tracking-wider">
                Valid AST Rate (VAST)
              </span>
              <ShieldCheck className="h-4 w-4 text-accent-primary" aria-hidden="true" />
            </div>
            <p className="mt-2 font-mono text-2xl font-bold tabular-nums text-accent-primary">
              {summary.vast_percentage.toFixed(1)}%
            </p>
            <p className="mt-1 text-[11px] text-text-secondary">
              {summary.vast_passed_count} of {summary.total_cases} queries passed the SQLGlot AST gate.
            </p>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface">
              <div
                className="h-full bg-accent-primary transition-all duration-300"
                style={{ width: `${Math.min(100, summary.vast_percentage)}%` }}
              />
            </div>
          </div>

          {/* 3. Average Latency */}
          <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-xs">
            <div className="flex items-center justify-between text-text-secondary">
              <span className="text-[11px] font-medium uppercase tracking-wider">
                Mean Latency
              </span>
              <Clock className="h-4 w-4 text-accent-secondary" aria-hidden="true" />
            </div>
            <p className="mt-2 font-mono text-2xl font-bold tabular-nums text-text-primary">
              {formatDurationMs(summary.avg_latency_ms)}
            </p>
            <p className="mt-1 text-[11px] text-text-secondary">
              Average generation + database round-trip time.
            </p>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface">
              <div className="h-full w-2/3 bg-accent-secondary" />
            </div>
          </div>

          {/* 4. Total Benchmark Cases */}
          <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-xs">
            <div className="flex items-center justify-between text-text-secondary">
              <span className="text-[11px] font-medium uppercase tracking-wider">
                Golden Suite Size
              </span>
              <Database className="h-4 w-4 text-status-warning" aria-hidden="true" />
            </div>
            <p className="mt-2 font-mono text-2xl font-bold tabular-nums text-text-primary">
              {summary.total_cases} Cases
            </p>
            <p className="mt-1 text-[11px] text-text-secondary">
              Curated business questions on live schema.
            </p>
            <div className="mt-3 flex gap-1 font-mono text-[10px] text-text-muted">
              <span>Easy: {summary.by_difficulty.easy?.total ?? 0}</span>
              <span>·</span>
              <span>Med: {summary.by_difficulty.medium?.total ?? 0}</span>
              <span>·</span>
              <span>Hard: {summary.by_difficulty.hard?.total ?? 0}</span>
            </div>
          </div>
        </div>
      ) : isLoading ? (
        <div className="flex h-36 items-center justify-center rounded-lg border border-border-subtle bg-card">
          <Loader2 className="h-6 w-6 animate-spin text-accent-primary" />
        </div>
      ) : null}

      {/* Difficulty Breakdown Cards */}
      {summary ? (
        <div className="grid gap-3 sm:grid-cols-3">
          {(["easy", "medium", "hard"] as const).map((diff) => {
            const stat = summary.by_difficulty[diff];
            if (!stat) return null;
            return (
              <div
                key={diff}
                className="rounded-lg border border-border-subtle bg-card p-3 shadow-xs"
              >
                <div className="flex items-center justify-between">
                  <Badge
                    variant={
                      diff === "easy" ? "cyan" : diff === "medium" ? "warning" : "indigo"
                    }
                  >
                    {diff.toUpperCase()}
                  </Badge>
                  <span className="font-mono text-xs font-semibold tabular-nums text-text-primary">
                    {stat.accuracy_percentage.toFixed(0)}%
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between text-[11px] text-text-secondary font-mono tabular-nums">
                  <span>Passed: {stat.passed} / {stat.total}</span>
                  <span>{stat.total - stat.passed === 0 ? "100% Match" : `${stat.total - stat.passed} Delta`}</span>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3">
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-medium text-text-secondary">Filter by:</span>
          {(["all", "easy", "medium", "hard"] as const).map((tier) => (
            <button
              key={tier}
              onClick={() => setSelectedDifficulty(tier)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-all ${
                selectedDifficulty === tier
                  ? "bg-accent-primary text-white shadow-xs"
                  : "bg-surface text-text-secondary hover:bg-card hover:text-text-primary"
              }`}
            >
              {tier.charAt(0).toUpperCase() + tier.slice(1)}
              {tier !== "all" && summary?.by_difficulty[tier]
                ? ` (${summary.by_difficulty[tier]?.total})`
                : tier === "all" && summary
                  ? ` (${summary.total_cases})`
                  : ""}
            </button>
          ))}
        </div>

        <div className="text-xs text-text-secondary font-mono">
          Showing {filteredResults.length} test cases
        </div>
      </div>

      {/* Benchmark Results Table */}
      <div className="overflow-hidden rounded-lg border border-border-subtle bg-card shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left text-xs">
            <thead className="border-b border-border-subtle bg-surface/80 text-text-secondary font-mono text-[11px]">
              <tr>
                <th scope="col" className="px-4 py-3">Case ID</th>
                <th scope="col" className="px-4 py-3">Natural Language Question</th>
                <th scope="col" className="px-3 py-3">Category</th>
                <th scope="col" className="px-3 py-3">Tier</th>
                <th scope="col" className="px-3 py-3">Status</th>
                <th scope="col" className="px-3 py-3 text-right">Rows</th>
                <th scope="col" className="px-3 py-3 text-right">Latency</th>
                <th scope="col" className="px-4 py-3 text-right">Inspection</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle/50">
              {filteredResults.map((item) => {
                const isExpanded = expandedCaseId === item.case_id;
                return (
                  <tr
                    key={item.case_id}
                    className="transition-colors hover:bg-card-hover/40"
                  >
                    <td colSpan={8} className="p-0">
                      <div className="flex items-center px-4 py-3">
                        {/* Case ID */}
                        <div className="w-24 shrink-0 font-mono text-[11px] font-semibold text-accent-secondary">
                          {item.case_id}
                        </div>

                        {/* Question */}
                        <div className="flex-1 pr-4 font-medium text-text-primary">
                          {item.question}
                        </div>

                        {/* Category */}
                        <div className="w-36 shrink-0 truncate text-[11px] text-text-secondary font-mono">
                          {item.category}
                        </div>

                        {/* Difficulty */}
                        <div className="w-20 shrink-0">
                          <Badge
                            variant={
                              item.difficulty === "easy"
                                ? "cyan"
                                : item.difficulty === "medium"
                                  ? "warning"
                                  : "indigo"
                            }
                          >
                            {item.difficulty}
                          </Badge>
                        </div>

                        {/* Status */}
                        <div className="w-32 shrink-0">
                          {item.status === "passed" ? (
                            <Badge variant="success">
                              <CheckCircle2 className="h-3 w-3" />
                              MATCH (EX)
                            </Badge>
                          ) : item.status === "blocked" ? (
                            <Badge variant="error">BLOCKED</Badge>
                          ) : (
                            <Badge variant="warning">MISMATCH</Badge>
                          )}
                        </div>

                        {/* Rows */}
                        <div className="w-24 shrink-0 text-right font-mono tabular-nums text-text-secondary">
                          {item.candidate_row_count !== null ? item.candidate_row_count : "—"} / {item.golden_row_count}
                        </div>

                        {/* Latency */}
                        <div className="w-20 shrink-0 text-right font-mono tabular-nums text-text-secondary">
                          {formatDurationMs(item.latency_ms)}
                        </div>

                        {/* Toggle */}
                        <div className="w-24 shrink-0 text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setExpandedCaseId(isExpanded ? null : item.case_id)
                            }
                            className="h-7 text-xs"
                          >
                            <span>{isExpanded ? "Hide" : "Diff"}</span>
                            {isExpanded ? (
                              <ChevronUp className="h-3 w-3" />
                            ) : (
                              <ChevronDown className="h-3 w-3" />
                            )}
                          </Button>
                        </div>
                      </div>

                      {/* Expanded Accordion: SQL Diff & Analysis */}
                      {isExpanded ? (
                        <div className="border-t border-border-subtle/80 bg-surface/60 p-4">
                          <div className="grid gap-4 lg:grid-cols-2">
                            {/* Candidate SQL */}
                            <div className="rounded-md border border-border-subtle bg-canvas p-3">
                              <div className="mb-2 flex items-center justify-between">
                                <span className="font-mono text-[11px] font-semibold text-accent-primary">
                                  Generated Candidate SQL
                                </span>
                                {item.generated_sql ? (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() =>
                                      handleCopy(`cand_${item.case_id}`, item.generated_sql ?? "")
                                    }
                                    className="h-6 px-2 text-[10px]"
                                  >
                                    <Copy className="h-3 w-3" />
                                    <span>
                                      {copiedSqlKey === `cand_${item.case_id}` ? "Copied" : "Copy"}
                                    </span>
                                  </Button>
                                ) : null}
                              </div>
                              <pre className="max-h-48 overflow-auto font-mono text-[11px] text-text-primary">
                                <code>{item.generated_sql || "— No SQL produced —"}</code>
                              </pre>
                            </div>

                            {/* Canonical Golden SQL */}
                            <div className="rounded-md border border-border-subtle bg-canvas p-3">
                              <div className="mb-2 flex items-center justify-between">
                                <span className="font-mono text-[11px] font-semibold text-status-success">
                                  Canonical Ground Truth SQL (Reference)
                                </span>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() =>
                                    handleCopy(`gold_${item.case_id}`, item.golden_sql)
                                  }
                                  className="h-6 px-2 text-[10px]"
                                >
                                  <Copy className="h-3 w-3" />
                                  <span>
                                    {copiedSqlKey === `gold_${item.case_id}` ? "Copied" : "Copy"}
                                  </span>
                                </Button>
                              </div>
                              <pre className="max-h-48 overflow-auto font-mono text-[11px] text-accent-secondary">
                                <code>{item.golden_sql}</code>
                              </pre>
                            </div>
                          </div>

                          {item.error_message ? (
                            <div className="mt-3 flex items-start gap-2 rounded-md border border-status-error/30 bg-status-error/10 p-2.5 text-[11px] text-status-error">
                              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                              <span>{item.error_message}</span>
                            </div>
                          ) : null}
                        </div>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
