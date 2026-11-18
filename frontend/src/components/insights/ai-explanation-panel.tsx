"use client";

import { BookOpen, Info, Lightbulb, Table2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { ExplanationResponse } from "@/types/api";

interface AiExplanationPanelProps {
  explanation: ExplanationResponse | null;
  generationRationale: string | null;
  assumptions: string[];
  selectedTables: string[];
  ambiguities: string[];
  warnings: string[];
}

export function AiExplanationPanel({
  explanation,
  generationRationale,
  assumptions,
  selectedTables,
  ambiguities,
  warnings,
}: AiExplanationPanelProps) {
  if (!explanation && !generationRationale && warnings.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-border-subtle bg-card px-6 py-10 text-center">
        <BookOpen className="h-6 w-6 text-text-secondary/60" aria-hidden="true" />
        <p className="mt-2.5 text-sm font-medium text-text-primary">
          No AI explanation for this run
        </p>
        <p className="mt-1 max-w-md text-xs text-text-secondary">
          Submit a natural-language question via Ask Detective to receive a grounded explanation of
          returned results.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {explanation ? (
        <div className="rounded-lg border border-border-subtle bg-card p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-primary">
              <Lightbulb className="h-3.5 w-3.5 text-accent-secondary" aria-hidden="true" />
              <span>Result Explanation</span>
            </h3>
            {explanation.suggested_chart !== "none" ? (
              <Badge variant="cyan">Suggested visual: {explanation.suggested_chart}</Badge>
            ) : null}
          </div>
          <p className="mt-2.5 text-sm leading-relaxed text-text-primary">{explanation.summary}</p>

          {explanation.key_findings.length > 0 ? (
            <div className="mt-4">
              <h4 className="font-mono text-[11px] uppercase tracking-wider text-text-secondary">
                Key Findings
              </h4>
              <ul className="mt-1.5 list-disc space-y-1 pl-5 text-xs leading-relaxed text-text-primary">
                {explanation.key_findings.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {explanation.caveats.length > 0 ? (
            <div className="mt-4 rounded-md border border-status-warning/30 bg-status-warning/10 p-3">
              <h4 className="font-mono text-[11px] uppercase tracking-wider text-status-warning">
                Caveats
              </h4>
              <ul className="mt-1 list-disc space-y-1 pl-5 text-xs text-text-primary">
                {explanation.caveats.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        {generationRationale || assumptions.length > 0 ? (
          <div className="rounded-lg border border-border-subtle bg-card p-4">
            <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-primary">
              <Info className="h-3.5 w-3.5 text-accent-primary" aria-hidden="true" />
              <span>SQL Rationale &amp; Assumptions</span>
            </h3>
            {generationRationale ? (
              <p className="mt-2 text-xs leading-relaxed text-text-secondary">
                {generationRationale}
              </p>
            ) : null}
            {assumptions.length > 0 ? (
              <ul className="mt-2.5 list-disc space-y-1 pl-5 text-xs text-text-primary">
                {assumptions.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}

        {selectedTables.length > 0 || ambiguities.length > 0 ? (
          <div className="rounded-lg border border-border-subtle bg-card p-4">
            <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-primary">
              <Table2 className="h-3.5 w-3.5 text-accent-secondary" aria-hidden="true" />
              <span>Schema Analyst Grounding</span>
            </h3>
            {selectedTables.length > 0 ? (
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {selectedTables.map((table) => (
                  <Badge key={table} variant="default">
                    {table}
                  </Badge>
                ))}
              </div>
            ) : null}
            {ambiguities.length > 0 ? (
              <ul className="mt-2.5 list-disc space-y-1 pl-5 text-xs text-status-warning">
                {ambiguities.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : null}
      </div>

      {warnings.length > 0 ? (
        <div className="rounded-md border border-status-warning/30 bg-status-warning/10 p-3 text-xs">
          <p className="font-mono text-[11px] font-semibold uppercase text-status-warning">
            Workflow Notices
          </p>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-text-primary">
            {warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
