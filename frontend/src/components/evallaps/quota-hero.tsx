"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  Clock,
  Gauge,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import { formatNumber } from "@/lib/format";
import type { QuotaOverviewResponse } from "@/types/evallaps";

interface QuotaHeroProps {
  overview: QuotaOverviewResponse;
}

function formatCountdown(totalSeconds: number): string {
  if (totalSeconds <= 0) return "00h 00m 00s";
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return `${String(hours).padStart(2, "0")}h ${String(minutes).padStart(2, "0")}m ${String(seconds).padStart(2, "0")}s`;
}

export function QuotaHero({ overview }: QuotaHeroProps) {
  const queryClient = useQueryClient();
  const [remainingSeconds, setRemainingSeconds] = useState(
    overview.seconds_until_daily_reset
  );

  useEffect(() => {
    setRemainingSeconds(overview.seconds_until_daily_reset);
  }, [overview.seconds_until_daily_reset]);

  useEffect(() => {
    const timer = setInterval(() => {
      setRemainingSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const resetMutation = useMutation({
    mutationFn: () => apiClient.resetQuotaCycle(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["evallaps-overview"] });
      void queryClient.invalidateQueries({ queryKey: ["evallaps-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["evallaps-balance"] });
      void queryClient.invalidateQueries({ queryKey: ["evallaps-models"] });
      void queryClient.invalidateQueries({ queryKey: ["evallaps-circuit-breaker"] });
    },
  });

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-card p-5 shadow-lg before:absolute before:inset-x-0 before:top-0 before:h-0.5 before:bg-gradient-to-r before:from-sky-400 before:via-cyan-400 before:to-emerald-400">
      {/* Top action & header row */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-500/15 text-sky-400">
            <Gauge className="h-5 w-5" aria-hidden="true" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-semibold tracking-tight text-white">
                Taux de Consommation &amp; Quotas
              </h2>
              <Badge variant="cyan" className="border-sky-400/40 text-sky-300 text-[10px] font-mono">
                Multi-Provider Pool
              </Badge>
              <span className="flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-2.5 py-0.5 font-mono text-[10px] font-medium text-emerald-300 border border-emerald-500/30">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Cycle Actif
              </span>
            </div>
          </div>
        </div>

        {/* Manual Reset Action Button */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => resetMutation.mutate()}
            disabled={resetMutation.isPending}
            className="gap-2 font-mono text-xs border-slate-700 bg-surface/80 hover:bg-surface text-slate-200 hover:border-sky-400 hover:text-white transition-all active:scale-[0.99]"
          >
            {resetMutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin text-sky-400" aria-hidden="true" />
            ) : (
              <RefreshCw className="h-3.5 w-3.5 text-cyan-400" aria-hidden="true" />
            )}
            <span>{resetMutation.isPending ? "Resynchronisation..." : "Réinitialiser / Sync Cycle"}</span>
          </Button>
        </div>
      </div>

      {/* 4-KPI Metric Grid */}
      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Card 1: Consommation Aujourd'hui */}
        <div className="rounded-lg border border-slate-800 bg-surface/70 p-4 transition-colors hover:border-sky-500/40">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300 font-medium">Tokens Aujourd&apos;hui</span>
            <Zap className="h-4 w-4 text-sky-400" aria-hidden="true" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold tracking-tight text-white tabular-nums">
              {formatNumber(overview.today_tokens)}
            </span>
            <span className="font-mono text-xs text-slate-400 tabular-nums">
              / {formatNumber(overview.today_quota_tokens)}
            </span>
          </div>

          {/* Progress bar */}
          <div className="mt-3">
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>Utilisation Jour</span>
              <span className="text-sky-300 font-semibold tabular-nums">{overview.today_usage_percentage}%</span>
            </div>
            <div className="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-slate-800/90 border border-slate-700/60 p-[1px]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-sky-400 to-cyan-300 transition-all duration-500"
                style={{ width: `${Math.min(100, overview.today_usage_percentage)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Card 2: Consommation Ce Mois */}
        <div className="rounded-lg border border-slate-800 bg-surface/70 p-4 transition-colors hover:border-indigo-500/40">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300 font-medium">Tokens ce Mois</span>
            <Activity className="h-4 w-4 text-violet-400" aria-hidden="true" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold tracking-tight text-white tabular-nums">
              {formatNumber(overview.month_tokens)}
            </span>
            <span className="font-mono text-xs text-slate-400 tabular-nums">
              / {formatNumber(overview.month_quota_tokens)}
            </span>
          </div>

          {/* Progress bar */}
          <div className="mt-3">
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>Utilisation Mensuelle</span>
              <span className="text-violet-300 font-semibold tabular-nums">{overview.month_usage_percentage}%</span>
            </div>
            <div className="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-slate-800/90 border border-slate-700/60 p-[1px]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-violet-400 transition-all duration-500"
                style={{ width: `${Math.min(100, overview.month_usage_percentage)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Card 3: Tokens Restants */}
        <div className="rounded-lg border border-slate-800 bg-surface/70 p-4 transition-colors hover:border-emerald-500/40">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300 font-medium">Tokens Restants</span>
            <ShieldCheck className="h-4 w-4 text-emerald-400" aria-hidden="true" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="font-mono text-2xl font-bold tracking-tight text-emerald-300 tabular-nums">
              {formatNumber(overview.today_remaining_tokens)}
            </span>
            <span className="rounded bg-emerald-500/15 px-2 py-0.5 font-mono text-[10px] text-emerald-300 border border-emerald-500/30">
              Optimal
            </span>
          </div>

          {/* Health details */}
          <div className="mt-3">
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>Marge de sécurité</span>
              <span className="text-emerald-300 font-semibold tabular-nums">
                {(100 - overview.today_usage_percentage).toFixed(1)}%
              </span>
            </div>
            <div className="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-slate-800/90 border border-slate-700/60 p-[1px]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-300 transition-all duration-500"
                style={{ width: `${Math.max(0, 100 - overview.today_usage_percentage)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Card 4: Compte à Rebours de Réinitialisation */}
        <div className="rounded-lg border border-slate-800 bg-surface/70 p-4 transition-colors hover:border-amber-500/40">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-mono text-[11px] uppercase tracking-wider text-slate-300 font-medium">Réinitialisation</span>
            <Clock className="h-4 w-4 text-amber-400 animate-pulse" aria-hidden="true" />
          </div>
          <div className="mt-2">
            <span className="font-mono text-2xl font-bold tracking-tight text-amber-300 tabular-nums">
              {formatCountdown(remainingSeconds)}
            </span>
          </div>

          {/* Cycle progression */}
          <div className="mt-3">
            <div className="flex justify-between text-[11px] font-mono text-slate-400">
              <span>Cycle Quotidien</span>
              <span className="text-amber-300 font-semibold tabular-nums">{overview.daily_cycle_percentage_elapsed}%</span>
            </div>
            <div className="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-slate-800/90 border border-slate-700/60 p-[1px]">
              <div
                className="h-full rounded-full bg-gradient-to-r from-amber-400 to-yellow-300 transition-all duration-500"
                style={{ width: `${overview.daily_cycle_percentage_elapsed}%` }}
              />
            </div>
          </div>
          <p className="mt-2 text-[11px] text-slate-400 font-mono">
            Reset quotidien 00:00 UTC
          </p>
        </div>
      </div>
    </div>
  );
}
