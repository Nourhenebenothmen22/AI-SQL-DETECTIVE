"use client";

import { CheckCircle2, ClipboardCheck, ShieldAlert, ShieldCheck, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { SecurityCheckResponse } from "@/types/api";

interface SecurityReviewPanelProps {
  securityStatus: "passed" | "blocked" | null;
  securityViolations: string[];
  securityChecks: SecurityCheckResponse[];
  enforcedLimit: number | null;
  limitWasInjected: boolean;
  limitWasClamped: boolean;
  reviewStatus: "approved" | "needs_revision" | null;
  reviewNotes: string[];
}

export function SecurityReviewPanel({
  securityStatus,
  securityViolations,
  securityChecks,
  enforcedLimit,
  limitWasInjected,
  limitWasClamped,
  reviewStatus,
  reviewNotes,
}: SecurityReviewPanelProps) {
  if (!securityStatus && !reviewStatus) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-border-subtle bg-card px-6 py-10 text-center">
        <ShieldCheck className="h-6 w-6 text-text-secondary/60" aria-hidden="true" />
        <p className="mt-2.5 text-sm font-medium text-text-primary">
          No security validation report yet
        </p>
        <p className="mt-1 max-w-md text-xs text-text-secondary">
          Click Validate or Run Read-Only in the SQL Editor, or submit a natural-language question
          to inspect deterministic SQLGlot AST checks.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {/* Independent Deterministic Security Gate */}
      <div className="rounded-lg border border-border-subtle bg-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-primary">
            {securityStatus === "blocked" ? (
              <ShieldAlert className="h-4 w-4 text-status-error" aria-hidden="true" />
            ) : (
              <ShieldCheck className="h-4 w-4 text-status-success" aria-hidden="true" />
            )}
            <span>Independent Security Gate (Deterministic)</span>
          </h3>
          {securityStatus === "passed" ? (
            <Badge variant="success">PASSED</Badge>
          ) : securityStatus === "blocked" ? (
            <Badge variant="error">BLOCKED</Badge>
          ) : null}
        </div>

        <p className="mt-1.5 text-[11px] text-text-secondary">
          Enforced via PostgreSQL SQLGlot AST parsing independent of LLM reasoning.
        </p>

        {enforcedLimit !== null ? (
          <div className="mt-3 flex flex-wrap gap-1.5">
            <Badge variant="cyan">Enforced LIMIT {enforcedLimit}</Badge>
            {limitWasInjected ? <Badge variant="default">LIMIT auto-injected</Badge> : null}
            {limitWasClamped ? <Badge variant="warning">LIMIT clamped to ceiling</Badge> : null}
          </div>
        ) : null}

        {securityViolations.length > 0 ? (
          <div
            role="alert"
            className="mt-3 rounded-md border border-status-error/40 bg-status-error/10 p-3"
          >
            <p className="font-mono text-[11px] font-semibold uppercase text-status-error">
              Violations ({securityViolations.length})
            </p>
            <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs text-text-primary">
              {securityViolations.map((violation, idx) => (
                <li key={idx}>{violation}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {securityChecks.length > 0 ? (
          <ul className="mt-3 space-y-1.5">
            {securityChecks.map((check) => (
              <li
                key={check.rule}
                className="flex items-start gap-2 rounded-md border border-border-subtle/70 bg-surface px-3 py-2 text-xs"
              >
                {check.passed ? (
                  <CheckCircle2
                    className="mt-0.5 h-3.5 w-3.5 shrink-0 text-status-success"
                    aria-hidden="true"
                  />
                ) : (
                  <XCircle
                    className="mt-0.5 h-3.5 w-3.5 shrink-0 text-status-error"
                    aria-hidden="true"
                  />
                )}
                <div className="min-w-0">
                  <p className="font-mono text-[11px] font-medium text-text-primary">
                    {check.rule}
                  </p>
                  <p className="text-[11px] text-text-secondary">{check.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      {/* Query Reviewer (Semantic Quality Only) */}
      <div className="rounded-lg border border-border-subtle bg-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-primary">
            <ClipboardCheck className="h-4 w-4 text-accent-primary" aria-hidden="true" />
            <span>Query Reviewer (Semantic Quality)</span>
          </h3>
          {reviewStatus === "approved" ? (
            <Badge variant="success">APPROVED</Badge>
          ) : reviewStatus === "needs_revision" ? (
            <Badge variant="warning">NEEDS REVISION</Badge>
          ) : (
            <Badge variant="default">MANUAL SQL</Badge>
          )}
        </div>

        <p className="mt-1.5 text-[11px] text-text-secondary">
          Evaluates join accuracy, aggregation logic, and schema alignment. Never treated as a
          security boundary.
        </p>

        {reviewNotes.length > 0 ? (
          <ul className="mt-3 space-y-2">
            {reviewNotes.map((note, idx) => (
              <li
                key={idx}
                className="rounded-md border border-border-subtle/70 bg-surface px-3 py-2 text-xs leading-relaxed text-text-primary"
              >
                {note}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-4 rounded-md border border-border-subtle/60 bg-surface/60 px-3 py-4 text-xs text-text-secondary">
            {reviewStatus
              ? "Query Reviewer approved without additional notes."
              : "Query Reviewer runs automatically during natural-language SQL generation."}
          </p>
        )}
      </div>
    </div>
  );
}
