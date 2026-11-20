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
      className="relative overflow-hidden rounded-lg border border-border-subtle bg-surface/90 shadow-sm transition-all duration-200"
    >
      {/* Top Industrial Chassis Accent Bar */}
      <div className="flex h-1 w-full items-center">
        <div className="h-full w-2/5 bg-accent-primary" />
        <div className="h-full w-2/5 bg-accent-secondary" />
        <div className="h-full w-1/5 bg-status-success" />
      </div>

      <div className="p-3">
        {/* Chassis Header: Enclave Identifier + Live Telemetry Status */}
        <div className="flex items-center justify-between border-b border-border-subtle/60 pb-2">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5 text-accent-secondary" aria-hidden="true" />
            <span className="font-mono text-[10px] font-semibold tracking-wider uppercase text-text-primary">
              SYS_GUARD // L4
            </span>
          </div>

          <div className="flex items-center gap-1.5 font-mono text-[10px]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-status-success/75 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-status-success" />
            </span>
            <span className="font-medium text-status-success">ENFORCING</span>
          </div>
        </div>

        {/* 3 Micro-Telemetry Hardware Cells */}
        <div className="mt-2.5 grid grid-cols-1 gap-1.5 font-mono text-[10px]">
          {/* Cell 1: AST Security Parser */}
          <div className="flex items-center justify-between rounded border border-border-subtle/70 bg-card/60 px-2 py-1.5">
            <div className="flex items-center gap-1.5 text-text-secondary">
              <Zap className="h-3 w-3 text-accent-secondary" aria-hidden="true" />
              <span>AST_GATE</span>
            </div>
            <span className="font-semibold text-text-primary">SQLGlot v25 · STRICT</span>
          </div>

          {/* Cell 2: PostgreSQL Role Isolation */}
          <div className="flex items-center justify-between rounded border border-border-subtle/70 bg-card/60 px-2 py-1.5">
            <div className="flex items-center gap-1.5 text-text-secondary">
              <Database className="h-3 w-3 text-accent-primary" aria-hidden="true" />
              <span>ROLE_ISO</span>
            </div>
            <span
              className={cn(
                "font-semibold",
                dbConnected ? "text-status-success" : "text-status-warning",
              )}
            >
              {dbConnected ? "pg_read_only (REVOKE DDL)" : "DB RECONNECTING"}
            </span>
          </div>

          {/* Cell 3: Circuit Breakers */}
          <div className="flex items-center justify-between rounded border border-border-subtle/70 bg-card/60 px-2 py-1.5">
            <div className="flex items-center gap-1.5 text-text-secondary">
              <Activity className="h-3 w-3 text-status-warning" aria-hidden="true" />
              <span>BOUNDS</span>
            </div>
            <span className="font-semibold tabular-nums text-text-primary">
              200 ROWS · 5000ms TTL
            </span>
          </div>
        </div>

        {/* Hardware AI Coprocessor Slot */}
        <div className="mt-2 flex items-center justify-between rounded border border-border-subtle/50 bg-canvas/70 px-2 py-1.5 font-mono text-[10px]">
          <div className="flex items-center gap-1.5 text-text-secondary">
            <Cpu className="h-3 w-3 text-accent-primary" aria-hidden="true" />
            <span>NEURAL_SLOT</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] tracking-tight text-accent-primary">
              {llmActive ? "▂▄▆█" : "░░░░"}
            </span>
            <span
              className={cn(
                "font-semibold uppercase",
                llmActive ? "text-text-primary" : "text-text-muted",
              )}
            >
              {llmActive ? `${health?.llm_provider ?? "AI"} ACTIVE` : "SQL ONLY"}
            </span>
          </div>
        </div>

        {/* Interactive Invariant Drawer Trigger */}
        <button
          type="button"
          onClick={() => setDetailsOpen((prev) => !prev)}
          aria-expanded={detailsOpen}
          aria-controls="defense-invariants-drawer"
          className="mt-2.5 flex w-full items-center justify-between rounded border border-border-subtle/80 bg-surface px-2 py-1 font-mono text-[10px] text-text-secondary transition-colors hover:border-accent-primary/60 hover:bg-card hover:text-text-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent-primary"
        >
          <span className="flex items-center gap-1">
            <Radio className="h-2.5 w-2.5 text-accent-secondary" aria-hidden="true" />
            <span>DEFENSE MATRIX</span>
          </span>
          <span className="flex items-center gap-0.5">
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
                className="flex items-start justify-between gap-1.5 rounded bg-canvas/50 p-1.5"
              >
                <div>
                  <p className="font-semibold text-text-primary">
                    <span className="text-status-success">✓ </span>
                    {inv.label}
                  </p>
                  <p className="text-[9px] leading-tight text-text-secondary">{inv.desc}</p>
                </div>
                <span className="shrink-0 text-[9px] text-text-muted">{inv.code}</span>
              </div>
            ))}
            <div className="pt-1 text-center font-mono text-[9px] text-text-muted">
              NON-BYPASSABLE DETERMINISTIC ENCLAVE
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
