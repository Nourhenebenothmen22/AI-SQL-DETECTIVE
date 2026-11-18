"use client";

import {
  AlertCircle,
  CheckCircle2,
  Circle,
  Loader2,
  RotateCw,
  ShieldAlert,
  Sparkles,
  Square,
} from "lucide-react";
import type { FormEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDurationMs } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { PrimaryStageId } from "@/types/api";

export interface StageProgressState {
  stage: PrimaryStageId;
  label: string;
  status: "idle" | "running" | "completed" | "retrying" | "blocked" | "error";
  attempt: number;
  durationMs: number | null;
  summary: string | null;
}

export const INITIAL_SIX_STAGES: StageProgressState[] = [
  {
    stage: "schema_analyst",
    label: "Schema Analyst",
    status: "idle",
    attempt: 0,
    durationMs: null,
    summary: null,
  },
  {
    stage: "sql_generator",
    label: "SQL Generator",
    status: "idle",
    attempt: 0,
    durationMs: null,
    summary: null,
  },
  {
    stage: "query_reviewer",
    label: "Query Reviewer",
    status: "idle",
    attempt: 0,
    durationMs: null,
    summary: null,
  },
  {
    stage: "security_gate",
    label: "Security Gate",
    status: "idle",
    attempt: 0,
    durationMs: null,
    summary: null,
  },
  {
    stage: "sql_executor",
    label: "SQL Executor",
    status: "idle",
    attempt: 0,
    durationMs: null,
    summary: null,
  },
  {
    stage: "result_explainer",
    label: "Result Explainer",
    status: "idle",
    attempt: 0,
    durationMs: null,
    summary: null,
  },
];

const STARTER_QUESTIONS = [
  "Top 10 products by delivered revenue and average review rating",
  "Monthly delivered order revenue and order count over the last 12 months",
  "Products currently below their reorder level grouped by warehouse",
  "Revenue breakdown by customer segment and payment method",
] as const;

interface NaturalLanguageInputProps {
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isStreaming: boolean;
  llmConfigured: boolean;
  stages: StageProgressState[];
  streamError: { code: string; message: string } | null;
}

function StageIcon({ status }: { status: StageProgressState["status"] }) {
  switch (status) {
    case "running":
      return <Loader2 className="h-3.5 w-3.5 animate-spin text-accent-primary" aria-hidden="true" />;
    case "completed":
      return <CheckCircle2 className="h-3.5 w-3.5 text-status-success" aria-hidden="true" />;
    case "retrying":
      return <RotateCw className="h-3.5 w-3.5 text-status-warning" aria-hidden="true" />;
    case "blocked":
      return <ShieldAlert className="h-3.5 w-3.5 text-status-error" aria-hidden="true" />;
    case "error":
      return <AlertCircle className="h-3.5 w-3.5 text-status-error" aria-hidden="true" />;
    default:
      return <Circle className="h-3.5 w-3.5 text-border-subtle" aria-hidden="true" />;
  }
}

export function NaturalLanguageInput({
  question,
  onQuestionChange,
  onSubmit,
  onCancel,
  isStreaming,
  llmConfigured,
  stages,
  streamError,
}: NaturalLanguageInputProps) {
  const handleFormSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!isStreaming && question.trim().length >= 3) {
      onSubmit();
    }
  };

  const hasAnyActivity = stages.some((stage) => stage.status !== "idle");

  return (
    <section className="rounded-lg border border-border-subtle bg-card p-4">
      <form onSubmit={handleFormSubmit} className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label
            htmlFor="nl-question-input"
            className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-primary"
          >
            <Sparkles className="h-3.5 w-3.5 text-accent-primary" aria-hidden="true" />
            <span>Ask in Natural Language</span>
          </label>
          <span className="font-mono text-[11px] text-text-secondary">
            {llmConfigured
              ? "SSE streaming · 6-stage verified pipeline"
              : "Configure LLM_API_KEY in root .env to enable AI generation"}
          </span>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row">
          <textarea
            id="nl-question-input"
            rows={2}
            value={question}
            onChange={(event) => onQuestionChange(event.target.value)}
            onKeyDown={(event) => {
              if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
                event.preventDefault();
                if (!isStreaming && question.trim().length >= 3) {
                  onSubmit();
                }
              }
            }}
            placeholder="Ask a question about the ecommerce database (e.g., Top 10 customers by lifetime delivered spend)..."
            aria-describedby="nl-question-hint"
            className="min-h-14 flex-1 resize-y rounded-md border border-border-subtle bg-canvas px-3 py-2 text-sm text-text-primary placeholder:text-text-secondary/70"
          />

          <div className="flex shrink-0 items-start gap-2 sm:flex-col">
            {isStreaming ? (
              <Button
                variant="danger"
                size="md"
                onClick={onCancel}
                className="w-full sm:w-36"
              >
                <Square className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Cancel</span>
              </Button>
            ) : (
              <Button
                type="submit"
                variant="primary"
                size="md"
                disabled={question.trim().length < 3}
                className="w-full sm:w-36"
              >
                <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Ask Detective</span>
              </Button>
            )}
          </div>
        </div>

        <div id="nl-question-hint" className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-text-secondary">Examples:</span>
          {STARTER_QUESTIONS.map((sample) => (
            <button
              key={sample}
              type="button"
              disabled={isStreaming}
              onClick={() => onQuestionChange(sample)}
              className="rounded border border-border-subtle bg-surface px-2 py-0.5 text-[11px] text-text-secondary transition-colors duration-150 hover:border-accent-primary/50 hover:text-text-primary disabled:opacity-50"
            >
              {sample}
            </button>
          ))}
        </div>
      </form>

      {hasAnyActivity ? (
        <div className="mt-4 border-t border-border-subtle pt-3.5">
          <div className="mb-2 flex items-center justify-between">
            <span className="font-mono text-[11px] uppercase tracking-wider text-text-secondary">
              Agent Execution Pipeline (6 Stages)
            </span>
            {isStreaming ? (
              <Badge variant="indigo">Streaming SSE</Badge>
            ) : null}
          </div>

          <ol className="grid gap-2 sm:grid-cols-2 xl:grid-cols-6">
            {stages.map((item, idx) => (
              <li
                key={item.stage}
                className={cn(
                  "rounded-md border px-2.5 py-2 transition-colors duration-150",
                  item.status === "running"
                    ? "border-accent-primary/70 bg-accent-primary/10"
                    : item.status === "completed"
                      ? "border-status-success/40 bg-surface"
                      : item.status === "retrying"
                        ? "border-status-warning/50 bg-status-warning/10"
                        : item.status === "blocked" || item.status === "error"
                          ? "border-status-error/50 bg-status-error/10"
                          : "border-border-subtle/70 bg-surface/60",
                )}
              >
                <div className="flex items-center justify-between gap-1.5">
                  <div className="flex min-w-0 items-center gap-1.5">
                    <StageIcon status={item.status} />
                    <span className="truncate text-xs font-medium text-text-primary">
                      {idx + 1}. {item.label}
                    </span>
                  </div>
                  {item.durationMs !== null ? (
                    <span className="shrink-0 font-mono text-[10px] tabular-nums text-text-secondary">
                      {formatDurationMs(item.durationMs)}
                    </span>
                  ) : null}
                </div>
                {item.summary ? (
                  <p className="mt-1 line-clamp-2 text-[11px] leading-snug text-text-secondary">
                    {item.summary}
                  </p>
                ) : (
                  <p className="mt-1 font-mono text-[10px] text-text-secondary/60">
                    {item.status === "running" ? "In progress..." : "Pending"}
                  </p>
                )}
              </li>
            ))}
          </ol>
        </div>
      ) : null}

      {streamError ? (
        <div
          role="alert"
          className="mt-3 flex items-start gap-2 rounded-md border border-status-error/40 bg-status-error/10 px-3 py-2.5 text-xs"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-status-error" aria-hidden="true" />
          <div>
            <p className="font-mono font-medium text-status-error">{streamError.code}</p>
            <p className="mt-0.5 text-text-primary">{streamError.message}</p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
