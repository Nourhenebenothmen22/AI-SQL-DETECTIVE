"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, BarChart3 } from "lucide-react";
import { useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { apiClient } from "@/lib/api-client";
import { formatCurrencyUsd, formatNumber } from "@/lib/format";
import type { TokenTimeSeriesPoint } from "@/types/evallaps";

const WINDOW_PRESETS = [
  { label: "24 Heures", value: 1 },
  { label: "7 Jours", value: 7 },
  { label: "30 Jours", value: 30 },
] as const;

interface TooltipPayloadItem {
  dataKey: string;
  name: string;
  value: number;
  color: string;
  payload: TokenTimeSeriesPoint;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadItem[];
}

function BurnChartTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const first = payload[0];
  if (!first) return null;
  const data = first.payload;

  return (
    <div className="rounded-lg border border-border-subtle bg-card p-3 shadow-xl">
      <p className="font-mono text-xs font-semibold text-text-primary">{data.label}</p>
      <div className="mt-2 space-y-1 font-mono text-[11px] tabular-nums">
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="h-2 w-2 rounded-full bg-sky-400" />
            Prompt Tokens :
          </span>
          <span className="font-medium text-white">{formatNumber(data.prompt_tokens)}</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="flex items-center gap-1.5 text-slate-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            Completion Tokens :
          </span>
          <span className="font-medium text-white">{formatNumber(data.completion_tokens)}</span>
        </div>
        <div className="flex items-center justify-between gap-4 border-t border-border-subtle/60 pt-1">
          <span className="text-slate-300 font-semibold">Total :</span>
          <span className="font-bold text-sky-400">{formatNumber(data.total_tokens)}</span>
        </div>
        <div className="flex items-center justify-between gap-4 text-emerald-400">
          <span>Économies USD :</span>
          <span>+{formatCurrencyUsd(data.savings_usd)}</span>
        </div>
      </div>
    </div>
  );
}

export function TokenBurnChart() {
  const [selectedWindow, setSelectedWindow] = useState<number>(30);

  const timeseriesQuery = useQuery({
    queryKey: ["evallaps-timeseries", selectedWindow],
    queryFn: ({ signal }) => apiClient.getTokenTimeseries(selectedWindow, signal),
    refetchInterval: 10000,
  });

  const points = timeseriesQuery.data?.points ?? [];
  const totalWindowTokens = timeseriesQuery.data?.total_tokens ?? 0;
  const totalWindowSavings = timeseriesQuery.data?.total_savings_usd ?? 0;

  return (
    <div className="rounded-xl border border-border-subtle bg-card p-5 shadow-sm">
      {/* Chart Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="rounded-md bg-accent-secondary/10 p-1.5 text-accent-secondary">
              <BarChart3 className="h-4 w-4" aria-hidden="true" />
            </div>
            <h3 className="text-sm font-semibold tracking-tight text-text-primary">
              Vélocité de Consommation Temporelle (Token Burn Rate)
            </h3>
          </div>
          <p className="text-xs text-text-secondary">
            Évolution continue de la consommation de tokens par intervalle temporel avec décomposition des entrées et sorties.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Quick Metrics */}
          <div className="flex items-center gap-3 font-mono text-xs tabular-nums">
            <span className="text-text-secondary">
              Total période : <strong className="text-accent-secondary">{formatNumber(totalWindowTokens)}</strong>
            </span>
            <span className="text-text-secondary">·</span>
            <span className="text-emerald-400">
              +{formatCurrencyUsd(totalWindowSavings)} économisés
            </span>
          </div>

          {/* Window Buttons */}
          <div
            role="group"
            aria-label="Granularité du graphique"
            className="inline-flex rounded-md border border-border-subtle bg-surface p-0.5"
          >
            {WINDOW_PRESETS.map((preset) => (
              <button
                key={preset.value}
                type="button"
                aria-pressed={selectedWindow === preset.value}
                onClick={() => setSelectedWindow(preset.value)}
                className={`min-h-7 rounded px-2.5 font-mono text-xs transition-colors ${
                  selectedWindow === preset.value
                    ? "bg-card text-text-primary shadow-xs font-semibold"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="mt-4 h-64 w-full">
        {points.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center text-xs text-text-secondary">
            <Activity className="h-8 w-8 text-border-subtle mb-2" aria-hidden="true" />
            <p>Aucune donnée de télémétrie sur cette fenêtre temporelle.</p>
            <p className="text-[11px] text-text-muted mt-0.5">
              Exécutez des requêtes dans le Workbench pour alimenter la série temporelle.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={points} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="skyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.45} />
                  <stop offset="95%" stopColor="#38BDF8" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="mintGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#34D399" stopOpacity={0.55} />
                  <stop offset="95%" stopColor="#34D399" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.5} vertical={false} />
              <XAxis
                dataKey="label"
                stroke="#94A3B8"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: "#334155" }}
              />
              <YAxis
                stroke="#94A3B8"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: "#334155" }}
                tickFormatter={(val: number) => (val >= 1000 ? `${(val / 1000).toFixed(0)}k` : String(val))}
              />
              <Tooltip content={<BurnChartTooltip />} />
              <Area
                type="monotone"
                dataKey="prompt_tokens"
                name="Prompt Tokens"
                stroke="#38BDF8"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#skyGradient)"
              />
              <Area
                type="monotone"
                dataKey="completion_tokens"
                name="Completion Tokens"
                stroke="#34D399"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#mintGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Footer Legend */}
      <div className="mt-3 flex items-center justify-between border-t border-border-subtle/50 pt-3 text-[11px] font-mono text-text-secondary">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-sky-400" />
            <span className="text-slate-300">Prompt Tokens (Entrée)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            <span className="text-slate-300">Completion Tokens (Génération IA)</span>
          </div>
        </div>
        <span>Données synchronisées en direct avec PostgreSQL</span>
      </div>
    </div>
  );
}
