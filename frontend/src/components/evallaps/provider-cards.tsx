"use client";

import { Activity, CheckCircle2, Clock, Cpu, RefreshCw } from "lucide-react";
import { formatCurrencyUsd, formatDurationMs, formatNumber } from "@/lib/format";
import type { ProviderRenewalMeta, ProviderUsageSummary } from "@/types/evallaps";

interface ProviderCardsProps {
  providers: ProviderUsageSummary[];
  catalog: ProviderRenewalMeta[];
}

function getCadenceBadge(type: string) {
  if (type === "sliding_window_1m") {
    return (
      <span className="flex items-center gap-1 rounded bg-blue-500/10 px-2 py-0.5 font-mono text-[10px] text-blue-400 border border-blue-500/20">
        <RefreshCw className="h-2.5 w-2.5 animate-spin-slow" aria-hidden="true" />
        Glissant 60s
      </span>
    );
  }
  if (type === "rolling_daily_24h") {
    return (
      <span className="flex items-center gap-1 rounded bg-emerald-500/10 px-2 py-0.5 font-mono text-[10px] text-emerald-400 border border-emerald-500/20">
        <Clock className="h-2.5 w-2.5" aria-hidden="true" />
        Quotidien 24h
      </span>
    );
  }
  return (
    <span className="flex items-center gap-1 rounded bg-purple-500/10 px-2 py-0.5 font-mono text-[10px] text-purple-400 border border-purple-500/20">
      <CheckCircle2 className="h-2.5 w-2.5" aria-hidden="true" />
      Mensuel
    </span>
  );
}

export function ProviderCards({ providers, catalog }: ProviderCardsProps) {
  const usageMap = new Map(providers.map((p) => [p.provider_name.toLowerCase(), p]));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <div className="rounded-md bg-accent-primary/10 p-1.5 text-accent-primary">
            <Cpu className="h-4 w-4" aria-hidden="true" />
          </div>
          <h3 className="text-sm font-semibold tracking-tight text-text-primary">
            Cartes de Santé &amp; Télémétrie des Fournisseurs LLM
          </h3>
        </div>
        <span className="font-mono text-xs text-text-secondary">
          {catalog.length} fournisseurs armés
        </span>
      </div>

      {/* Grid of sleek cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {catalog.map((meta) => {
          const usage = usageMap.get(meta.provider_name.toLowerCase());
          const totalTokens = usage?.total_tokens ?? 0;
          const totalSavings = usage?.estimated_savings_usd ?? 0;
          const successCalls = usage?.success_calls ?? 0;
          const avgLatency = usage?.avg_latency_ms ?? 0;

          return (
            <div
              key={meta.provider_name}
              className="flex flex-col justify-between rounded-lg border border-slate-800 bg-card p-4 transition-all hover:border-sky-500/40 hover:bg-card-hover"
            >
              <div>
                {/* Card Top */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h4 className="text-xs font-semibold text-slate-100">{meta.display_name}</h4>
                    <span className="font-mono text-[10px] text-slate-400 uppercase">
                      {meta.provider_name}
                    </span>
                  </div>
                  {getCadenceBadge(meta.renewal_type)}
                </div>

                {/* Tokens counter */}
                <div className="mt-3">
                  <div className="flex items-baseline justify-between font-mono text-xs tabular-nums">
                    <span className="font-bold text-sky-400">
                      {formatNumber(totalTokens)}
                    </span>
                    <span className="text-[10px] text-slate-400">tokens</span>
                  </div>
                  {/* Neon track */}
                  <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-slate-800/90 border border-slate-700/50 p-[0.5px]">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-sky-400 to-cyan-300"
                      style={{ width: `${Math.min(100, Math.max(2, (totalTokens / 500000) * 100))}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Micro-metrics bottom row */}
              <div className="mt-4 flex items-center justify-between border-t border-slate-800 pt-2 font-mono text-[10px] text-slate-400 tabular-nums">
                <span className="flex items-center gap-1">
                  <Activity className="h-3 w-3 text-emerald-400" aria-hidden="true" />
                  {successCalls} reqs
                </span>
                <span>{avgLatency > 0 ? formatDurationMs(avgLatency) : "—"}</span>
                <span className="font-semibold text-emerald-400">
                  +{formatCurrencyUsd(totalSavings)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
