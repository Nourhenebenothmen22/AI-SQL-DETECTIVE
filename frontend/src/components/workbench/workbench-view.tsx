"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BookOpen, Coins, Gauge, ShieldCheck, TableProperties } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { AiExplanationPanel } from "@/components/insights/ai-explanation-panel";
import {
  OptimizationPanel,
  type ParallelOptimizationState,
} from "@/components/insights/optimization-panel";
import { SecurityReviewPanel } from "@/components/insights/security-review-panel";
import { useConnection } from "@/components/providers/connection-provider";
import { SchemaExplorer } from "@/components/schema/schema-explorer";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  INITIAL_SIX_STAGES,
  NaturalLanguageInput,
  type StageProgressState,
} from "@/components/workbench/natural-language-input";
import { ResultsTable } from "@/components/workbench/results-table";
import { SqlEditor } from "@/components/workbench/sql-editor";
import { apiClient, ApiClientError } from "@/lib/api-client";
import { formatCurrencyUsd, formatNumber } from "@/lib/format";
import type {
  AskQueryResponse,
  ExecuteSQLResponse,
  ExplanationResponse,
  OptimizationRecommendationResponse,
  PlanSummaryResponse,
  PrimaryStageId,
  QueryClassificationResponse,
  SecurityCheckResponse,
} from "@/types/api";

const DEFAULT_SQL = `SELECT
  c.segment,
  COUNT(o.id) AS order_count,
  ROUND(SUM(o.total_amount), 2) AS total_revenue
FROM ecommerce.orders o
JOIN ecommerce.customers c ON c.id = o.customer_id
WHERE o.status = 'delivered'
GROUP BY c.segment
ORDER BY total_revenue DESC;`;

interface WorkbenchResultState {
  classification: QueryClassificationResponse | null;
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  wasTruncated: boolean;
  enforcedLimit: number | null;
  limitWasInjected: boolean;
  limitWasClamped: boolean;
  executionTimeMs: number | null;
  executionError: string | null;
  securityStatus: "passed" | "blocked" | null;
  securityViolations: string[];
  securityChecks: SecurityCheckResponse[];
  reviewStatus: "approved" | "needs_revision" | null;
  reviewNotes: string[];
  explanation: ExplanationResponse | null;
  generationRationale: string | null;
  assumptions: string[];
  selectedTables: string[];
  ambiguities: string[];
  explainPlan: Record<string, unknown>[] | Record<string, unknown> | null;
  planSummary: PlanSummaryResponse | null;
  optimizations: OptimizationRecommendationResponse[];
  warnings: string[];
  totalTokens: number | null;
  estimatedSavingsUsd: number | null;
}

const EMPTY_RESULT: WorkbenchResultState = {
  classification: null,
  columns: [],
  rows: [],
  rowCount: 0,
  wasTruncated: false,
  enforcedLimit: null,
  limitWasInjected: false,
  limitWasClamped: false,
  executionTimeMs: null,
  executionError: null,
  securityStatus: null,
  securityViolations: [],
  securityChecks: [],
  reviewStatus: null,
  reviewNotes: [],
  explanation: null,
  generationRationale: null,
  assumptions: [],
  selectedTables: [],
  ambiguities: [],
  explainPlan: null,
  planSummary: null,
  optimizations: [],
  warnings: [],
  totalTokens: null,
  estimatedSavingsUsd: null,
};

function resetSixStages(): StageProgressState[] {
  return INITIAL_SIX_STAGES.map((stage) => ({ ...stage }));
}

export function WorkbenchView() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const runIdParam = searchParams.get("runId");
  const qParam = searchParams.get("q");
  const { connectionId, health } = useConnection();

  const [question, setQuestion] = useState(qParam ?? "");
  const [sql, setSql] = useState(DEFAULT_SQL);
  const [activeTab, setActiveTab] = useState("results");
  const [stages, setStages] = useState<StageProgressState[]>(resetSixStages);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState<{ code: string; message: string } | null>(null);
  const [optimizationState, setOptimizationState] = useState<ParallelOptimizationState>({
    status: "idle",
    durationMs: null,
  });
  const [result, setResult] = useState<WorkbenchResultState>(EMPTY_RESULT);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Load historical run into Workbench when navigated via /?runId=<uuid>
  const historyDetailQuery = useQuery({
    queryKey: ["history-detail", runIdParam],
    queryFn: ({ signal }) => apiClient.getHistoryDetail(runIdParam ?? "", signal),
    enabled: Boolean(runIdParam),
  });

  useEffect(() => {
    if (qParam) {
      setQuestion(qParam);
    }
  }, [qParam]);

  useEffect(() => {
    const detail = historyDetailQuery.data;
    if (!detail) return;
    if (detail.natural_language_prompt) {
      setQuestion(detail.natural_language_prompt);
    }
    if (detail.validated_sql || detail.generated_sql) {
      setSql(detail.validated_sql ?? detail.generated_sql ?? "");
    }
    setResult({
      ...EMPTY_RESULT,
      rowCount: detail.row_count ?? 0,
      wasTruncated: detail.was_truncated,
      executionTimeMs: detail.execution_time_ms,
      securityStatus: detail.security_status,
      securityViolations: detail.security_violations,
      reviewStatus:
        detail.review_status === "approved" || detail.review_status === "needs_revision"
          ? detail.review_status
          : null,
      explanation: detail.explanation_text
        ? {
            summary: detail.explanation_text,
            key_findings: [],
            caveats: ["Reloaded from query history. Click Run Read-Only to refresh live rows."],
            suggested_chart: "none",
          }
        : null,
      explainPlan: detail.explain_plan,
      optimizations: detail.optimizations,
    });
    setOptimizationState({
      status: detail.optimizations.length > 0 ? "completed" : "idle",
      durationMs: null,
    });
  }, [historyDetailQuery.data]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const validateMutation = useMutation({
    mutationFn: () => apiClient.validateSql({ sql, connection_id: connectionId }),
    onSuccess: (data) => {
      setStreamError(null);
      setResult((prev) => ({
        ...prev,
        securityStatus: data.security_status,
        securityViolations: data.violations,
        securityChecks: data.checks,
        enforcedLimit: data.enforced_limit,
        limitWasInjected: data.limit_was_injected,
        limitWasClamped: data.limit_was_clamped,
      }));
      setActiveTab("security");
    },
    onError: (err) => {
      setStreamError({
        code: "validation_error",
        message: err instanceof Error ? err.message : "Unable to validate SQL.",
      });
    },
  });

  const executeMutation = useMutation({
    mutationFn: () =>
      apiClient.executeSql({
        sql,
        connection_id: connectionId,
        include_explain: true,
      }),
    onSuccess: (data: ExecuteSQLResponse) => {
      setStreamError(null);
      const deterministicOptimizations: OptimizationRecommendationResponse[] = (
        data.plan_summary?.findings ?? []
      ).map((finding) => ({
        severity:
          finding.severity === "high" || finding.severity === "warning"
            ? finding.severity
            : "info",
        category: finding.category,
        title: finding.title,
        detail: finding.detail,
        suggestion: finding.suggestion,
        suggested_sql_or_index: null,
      }));

      setResult({
        ...EMPTY_RESULT,
        columns: data.columns,
        rows: data.rows,
        rowCount: data.row_count,
        wasTruncated: data.was_truncated,
        enforcedLimit: data.enforced_limit,
        limitWasInjected: data.limit_was_injected,
        limitWasClamped: data.limit_was_clamped,
        executionTimeMs: data.execution_time_ms,
        executionError: data.execution_error,
        securityStatus: data.security_status,
        securityViolations: data.security_violations,
        securityChecks: data.security_checks,
        explainPlan: data.explain_plan,
        planSummary: data.plan_summary,
        optimizations: deterministicOptimizations,
        warnings: data.warnings,
      });
      setOptimizationState({
        status: data.plan_summary ? "partial" : "skipped",
        durationMs: null,
      });
      setActiveTab(data.security_status === "blocked" ? "security" : "results");
      void queryClient.invalidateQueries({ queryKey: ["history"] });
      void queryClient.invalidateQueries({ queryKey: ["analytics"] });
    },
    onError: (err) => {
      setStreamError({
        code: "execution_request_error",
        message: err instanceof Error ? err.message : "Failed to execute SQL query.",
      });
    },
  });

  const updateStage = (
    stageId: PrimaryStageId,
    updater: (current: StageProgressState) => StageProgressState,
  ) => {
    setStages((prev) => prev.map((item) => (item.stage === stageId ? updater(item) : item)));
  };

  const applyFinalAskResult = (final: AskQueryResponse) => {
    if (final.validated_sql || final.candidate_sql) {
      setSql(final.validated_sql ?? final.candidate_sql ?? "");
    }
    setResult({
      classification: final.classification ?? null,
      columns: final.columns,
      rows: final.rows,
      rowCount: final.row_count,
      wasTruncated: final.was_truncated,
      enforcedLimit: final.enforced_limit,
      limitWasInjected: final.limit_was_injected,
      limitWasClamped: final.limit_was_clamped,
      executionTimeMs: final.execution_time_ms,
      executionError: final.execution_error,
      securityStatus: final.security_status,
      securityViolations: final.security_violations,
      securityChecks: final.security_checks,
      reviewStatus: final.review_status,
      reviewNotes: final.review_notes,
      explanation: final.explanation,
      generationRationale: final.generation_rationale,
      assumptions: final.assumptions,
      selectedTables: final.selected_tables,
      ambiguities: final.ambiguities,
      explainPlan: final.explain_plan,
      planSummary: final.plan_summary,
      optimizations: final.optimizations,
      warnings: final.warnings,
      totalTokens: final.total_tokens ?? null,
      estimatedSavingsUsd: final.estimated_savings_usd ?? null,
    });
    setOptimizationState((prev) => ({
      status: final.optimization_status,
      durationMs: prev.durationMs,
    }));
    if (final.security_status === "blocked") {
      setActiveTab("security");
    } else if (final.execution_status === "success") {
      setActiveTab("results");
    }
    void queryClient.invalidateQueries({ queryKey: ["history"] });
    void queryClient.invalidateQueries({ queryKey: ["analytics"] });
  };

  const handleAskSubmit = async () => {
    if (!question.trim() || isStreaming) return;
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setIsStreaming(true);
    setStreamError(null);
    setStages(resetSixStages());
    setOptimizationState({ status: "idle", durationMs: null });

    try {
      await apiClient.streamAskQuery(
        {
          question: question.trim(),
          connection_id: connectionId,
          include_explain: true,
        },
        {
          onStageStarted: (event) => {
            updateStage(event.stage, (item) => ({
              ...item,
              status: "running",
              attempt: event.attempt,
            }));
          },
          onStageCompleted: (event) => {
            updateStage(event.stage, (item) => ({
              ...item,
              status: event.status,
              attempt: event.attempt,
              durationMs: event.duration_ms,
              summary: event.summary,
            }));
          },
          onStageRetry: (event) => {
            updateStage(event.stage, (item) => ({
              ...item,
              status: "retrying",
              attempt: event.attempt,
              summary: event.reason,
            }));
          },
          onSecurityBlocked: (event) => {
            setResult((prev) => ({
              ...prev,
              securityStatus: "blocked",
              securityViolations: event.violations,
            }));
            setActiveTab("security");
          },
          onOptimizationStarted: () => {
            setOptimizationState({ status: "running", durationMs: null });
          },
          onOptimizationCompleted: (event) => {
            setOptimizationState({
              status: event.status,
              durationMs: event.duration_ms,
            });
            setResult((prev) => ({
              ...prev,
              optimizations: event.recommendations,
            }));
          },
          onFinalResult: (final) => {
            applyFinalAskResult(final);
          },
          onError: (err) => {
            setStreamError(err);
          },
        },
        controller.signal,
      );
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setStreamError({
          code: "cancelled",
          message: "Request cancelled. Any in-flight database query was signalled to abort.",
        });
      } else if (err instanceof ApiClientError) {
        setStreamError({ code: `http_${err.status}`, message: err.detail });
      } else {
        setStreamError({
          code: "network_error",
          message: err instanceof Error ? err.message : "Failed to connect to SSE stream.",
        });
      }
    } finally {
      setIsStreaming(false);
    }
  };

  const handleCancelStream = () => {
    abortControllerRef.current?.abort();
  };

  const handleInsertIdentifier = (snippet: string) => {
    setSql((prev) => (prev.trim() ? `${prev.trimEnd()} ${snippet}` : snippet));
  };

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-4 p-4 lg:p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-text-primary">
            SQL Detective Workbench
          </h1>
          <p className="text-xs text-text-secondary">
            Explore introspected PostgreSQL schemas, generate or write read-only SQL, inspect
            deterministic security checks, and analyze EXPLAIN (FORMAT JSON) plans.
          </p>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[288px_minmax(0,1fr)]">
        {/* Left: Live PostgreSQL Schema Explorer */}
        <div className="xl:h-[calc(100dvh-140px)] xl:sticky xl:top-20">
          <SchemaExplorer
            connectionId={connectionId}
            onInsertIdentifier={handleInsertIdentifier}
          />
        </div>

        {/* Right: NL Prompt + Monaco SQL Editor + Tabbed Inspector */}
        <div className="min-w-0 space-y-4">
          <NaturalLanguageInput
            question={question}
            onQuestionChange={setQuestion}
            onSubmit={() => void handleAskSubmit()}
            onCancel={handleCancelStream}
            isStreaming={isStreaming}
            llmConfigured={Boolean(health?.llm_configured)}
            stages={stages}
            streamError={streamError}
          />

          <SqlEditor
            sql={sql}
            onSqlChange={setSql}
            onValidate={() => validateMutation.mutate()}
            onExecute={() => executeMutation.mutate()}
            isValidating={validateMutation.isPending}
            isExecuting={executeMutation.isPending}
            securityStatus={result.securityStatus}
            enforcedLimit={result.enforcedLimit}
          />

          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <TabsList aria-label="Query inspection panels">
                <TabsTrigger value="results">
                  <TableProperties className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Results</span>
                  {result.columns.length > 0 ? (
                    <Badge variant="default">{result.rowCount}</Badge>
                  ) : null}
                </TabsTrigger>

                <TabsTrigger value="explanation">
                  <BookOpen className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>AI Explanation</span>
                </TabsTrigger>

                <TabsTrigger value="security">
                  <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Security &amp; Review</span>
                  {result.securityStatus === "passed" ? (
                    <Badge variant="success">Pass</Badge>
                  ) : result.securityStatus === "blocked" ? (
                    <Badge variant="error">Blocked</Badge>
                  ) : null}
                </TabsTrigger>

                <TabsTrigger value="optimization">
                  <Gauge className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Optimization</span>
                  {optimizationState.status === "running" ? (
                    <Badge variant="cyan">Running</Badge>
                  ) : result.optimizations.length > 0 ? (
                    <Badge variant="warning">{result.optimizations.length}</Badge>
                  ) : null}
                </TabsTrigger>
              </TabsList>

              {result.totalTokens && result.totalTokens > 0 ? (
                <div className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 font-mono text-[11px] text-emerald-300">
                  <Coins className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
                  <span>{formatNumber(result.totalTokens)} tokens</span>
                  <span className="text-emerald-500/60">·</span>
                  <span className="font-semibold text-emerald-400">
                    +{formatCurrencyUsd(result.estimatedSavingsUsd)} économisés
                  </span>
                </div>
              ) : null}
            </div>

            <TabsContent value="results">
              <ResultsTable
                columns={result.columns}
                rows={result.rows}
                rowCount={result.rowCount}
                wasTruncated={result.wasTruncated}
                enforcedLimit={result.enforcedLimit}
                executionTimeMs={result.executionTimeMs}
                executionError={result.executionError}
                isLoading={executeMutation.isPending}
              />
            </TabsContent>

            <TabsContent value="explanation">
              <AiExplanationPanel
                classification={result.classification}
                explanation={result.explanation}
                generationRationale={result.generationRationale}
                assumptions={result.assumptions}
                selectedTables={result.selectedTables}
                ambiguities={result.ambiguities}
                warnings={result.warnings}
              />
            </TabsContent>

            <TabsContent value="security">
              <SecurityReviewPanel
                securityStatus={result.securityStatus}
                securityViolations={result.securityViolations}
                securityChecks={result.securityChecks}
                enforcedLimit={result.enforcedLimit}
                limitWasInjected={result.limitWasInjected}
                limitWasClamped={result.limitWasClamped}
                reviewStatus={result.reviewStatus}
                reviewNotes={result.reviewNotes}
              />
            </TabsContent>

            <TabsContent value="optimization">
              <OptimizationPanel
                optimizationState={optimizationState}
                recommendations={result.optimizations}
                planSummary={result.planSummary}
                explainPlan={result.explainPlan}
              />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
