"use client";

import {
  Activity,
  ChevronDown,
  ChevronUp,
  Cpu,
  Database,
  Radio,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/utils";
import type { HealthResponse } from "@/types/api";

interface DeterministicGuardHudProps {
  readonly health: HealthResponse | undefined;
}

const DEFENSE_INVARIANTS = [
  { code: "RULE_01", label: "AST Parse Gate", desc: "SQLGlot 100% token tree validation" },
  { code: "RULE_02", label: "Anti-Mutation", desc: "DROP, ALTER, UPDATE, DELETE strictly banned" },
  { code: "RULE_03", label: "Anti-Chaining", desc: "Semicolon multi-statement injection denied" },
  { code: "RULE_04", label: "Catalog Isolation", desc: "pg_catalog & OS filesystem evasion blocked" },
  { code: "RULE_05", label: "Bounded Execution", desc: "Forced LIMIT 200 & 5000ms hard timeout" },
] as const;

export function DeterministicGuardHud({ health }: DeterministicGuardHudProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);

  const dbConnected = health?.database_status === "connected";
  const llmActive = health?.llm_configured ?? false;

  return (
    <section
      aria-label="Security and System Telemetry"
      className="relative overflow-hidden rounded-lg border border-border-subtle bg-surface/95 shadow-sm transition-all duration-200"
    >
      {/* Top Industrial Chassis Accent Bar */}
      <div className="flex h-1 w-full items-center">
        <div className="h-full w-2/5 bg-accent-primary" />
        <div className="h-full w-2/5 bg-accent-secondary" />
        <div className="h-full w-1/5 bg-status-success" />
      </div>

      <div className="p-2.5">
        {/* Chassis Header: Enclave Identifier + Live Telemetry Status */}
        <div className="flex items-center justify-between border-b border-border-subtle/60 pb-2">
          <div className="flex items-center gap-1.5 min-w-0">
            <ShieldCheck className="h-3.5 w-3.5 text-accent-secondary shrink-0" aria-hidden="true" />
            <span className="font-mono text-[10px] font-semibold tracking-wider uppercase text-text-primary truncate">
              SYS_GUARD // L4
            </span>
          </div>

          <div className="flex items-center gap-1.5 font-mono text-[10px] shrink-0">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-status-success/75 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-status-success" />
            </span>
            <span className="font-semibold text-status-success">ENFORCING</span>
          </div>
        </div>

        {/* 2x2 Telemetry Grid: Micro-Cells without text wrapping */}
        <div className="mt-2 grid grid-cols-2 gap-1.5 font-mono">
          {/* Cell 1: AST Engine */}
          <div className="flex flex-col rounded border border-border-subtle/70 bg-card/60 p-2 min-w-0">
            <div className="flex items-center gap-1 text-[9px] text-text-secondary truncate">
              <Zap className="h-2.5 w-2.5 text-accent-secondary shrink-0" aria-hidden="true" />
              <span className="truncate">AST_GATE</span>
            </div>
            <p className="mt-1 text-[11px] font-semibold text-text-primary truncate leading-none">
              SQLGlot v25
            </p>
            <span className="mt-1 inline-block text-[8px] font-medium tracking-wider text-accent-secondary uppercase truncate leading-none">
              STRICT L4
            </span>
          </div>

          {/* Cell 2: PostgreSQL Role */}
          <div className="flex flex-col rounded border border-border-subtle/70 bg-card/60 p-2 min-w-0">
            <div className="flex items-center gap-1 text-[9px] text-text-secondary truncate">
              <Database className="h-2.5 w-2.5 text-accent-primary shrink-0" aria-hidden="true" />
              <span className="truncate">PG_ROLE</span>
            </div>
            <p className="mt-1 text-[11px] font-semibold text-text-primary truncate leading-none">
              read_only
            </p>
            <span
              className={cn(
                "mt-1 inline-block text-[8px] font-medium tracking-wider uppercase truncate leading-none",
                dbConnected ? "text-status-success" : "text-status-warning",
              )}
            >
              {dbConnected ? "REVOKE DDL" : "OFFLINE"}
            </span>
          </div>

          {/* Cell 3: Circuit Breakers */}
          <div className="flex flex-col rounded border border-border-subtle/70 bg-card/60 p-2 min-w-0">
            <div className="flex items-center gap-1 text-[9px] text-text-secondary truncate">
              <Activity className="h-2.5 w-2.5 text-status-warning shrink-0" aria-hidden="true" />
              <span className="truncate">BOUNDS</span>
            </div>
            <p className="mt-1 text-[11px] font-semibold tabular-nums text-text-primary truncate leading-none">
              200 ROWS
            </p>
            <span className="mt-1 inline-block text-[8px] font-medium tracking-wider text-status-warning uppercase truncate leading-none">
              5000ms TTL
            </span>
          </div>

          {/* Cell 4: AI Core */}
          <div className="flex flex-col rounded border border-border-subtle/70 bg-card/60 p-2 min-w-0">
            <div className="flex items-center gap-1 text-[9px] text-text-secondary truncate">
              <Cpu className="h-2.5 w-2.5 text-accent-primary shrink-0" aria-hidden="true" />
              <span className="truncate">AI_CORE</span>
            </div>
            <p className="mt-1 text-[11px] font-semibold text-text-primary truncate leading-none">
              {llmActive ? "GPT-4o" : "OFFLINE"}
            </p>
            <span
              className={cn(
                "mt-1 inline-block text-[8px] font-medium tracking-wider uppercase truncate leading-none",
                llmActive ? "text-accent-primary" : "text-text-muted",
              )}
            >
              {llmActive ? "STREAMING" : "SQL ONLY"}
            </span>
          </div>
        </div>

        {/* Interactive Invariant Drawer Trigger */}
        <button
          type="button"
          onClick={() => setDetailsOpen((prev) => !prev)}
          aria-expanded={detailsOpen}
          aria-controls="defense-invariants-drawer"
          className="mt-2 flex w-full items-center justify-between rounded border border-border-subtle/80 bg-surface px-2 py-1.5 font-mono text-[10px] text-text-secondary transition-colors hover:border-accent-primary/60 hover:bg-card hover:text-text-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-primary"
        >
          <span className="flex items-center gap-1.5 truncate">
            <Radio className="h-2.5 w-2.5 text-accent-secondary shrink-0" aria-hidden="true" />
            <span className="font-semibold tracking-wider">DEFENSE MATRIX</span>
          </span>
          <span className="flex items-center gap-1 shrink-0 text-[9px] font-semibold">
            <span>{detailsOpen ? "COLLAPSE" : "INSPECT"}</span>
            {detailsOpen ? (
              <ChevronUp className="h-3 w-3" aria-hidden="true" />
            ) : (
              <ChevronDown className="h-3 w-3" aria-hidden="true" />
            )}
          </span>
        </button>

        {/* Collapsible Inspection Panel */}
        {detailsOpen ? (
          <div
            id="defense-invariants-drawer"
            className="mt-2 space-y-1.5 border-t border-border-subtle/60 pt-2 font-mono text-[10px] animate-in fade-in duration-150"
          >
            {DEFENSE_INVARIANTS.map((inv) => (
              <div
                key={inv.code}
                className="flex items-start justify-between gap-1.5 rounded bg-canvas/60 p-1.5"
              >
                <div className="min-w-0">
                  <p className="font-semibold text-text-primary truncate">
                    <span className="text-status-success">✓ </span>
                    {inv.label}
                  </p>
                  <p className="text-[9px] leading-tight text-text-secondary">{inv.desc}</p>
                </div>
                <span className="shrink-0 text-[8px] text-text-muted">{inv.code}</span>
              </div>
            ))}
            <div className="pt-1 text-center font-mono text-[8px] text-text-muted uppercase tracking-wider">
              NON-BYPASSABLE DETERMINISTIC ENCLAVE
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
