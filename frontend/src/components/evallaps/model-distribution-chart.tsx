"use client";

import { PieChart as PieChartIcon } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

import { formatNumber } from "@/lib/format";
import type { ModelUsageSummary } from "@/types/evallaps";

const PALETTE = [
  "#38BDF8", // Sky Blue
  "#34D399", // Mint Green
  "#FBBF24", // Warm Amber
  "#A78BFA", // Soft Lavender
  "#22D3EE", // Bright Cyan
  "#FB7185", // Soft Rose
  "#818CF8", // Bright Indigo
  "#2DD4BF", // Soft Teal
];

interface ModelDistributionChartProps {
  models: ModelUsageSummary[];
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    payload: {
      model_name: string;
      provider_name: string;
      total_tokens: number;
      percentage: number;
    };
  }>;
}

function CustomDonutTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const item = payload[0];
  if (!item) return null;
  const data = item.payload;

  return (
    <div className="rounded-lg border border-border-subtle bg-card p-3 shadow-xl font-mono text-xs">
      <p className="font-semibold text-text-primary">{data.model_name}</p>
      <p className="text-[11px] text-text-secondary uppercase">{data.provider_name}</p>
      <div className="mt-2 flex items-center justify-between gap-4 border-t border-slate-700/60 pt-1.5 tabular-nums">
        <span className="text-slate-300">Tokens :</span>
        <span className="font-bold text-sky-400">{formatNumber(data.total_tokens)}</span>
      </div>
      <div className="flex items-center justify-between gap-4 text-emerald-300 tabular-nums">
        <span>Part du pool :</span>
        <span>{data.percentage.toFixed(1)}%</span>
      </div>
    </div>
  );
}

export function ModelDistributionChart({ models }: ModelDistributionChartProps) {
  const totalTokens = models.reduce((acc, m) => acc + m.total_tokens, 0);

  const chartData = models
    .filter((m) => m.total_tokens > 0)
    .map((m) => ({
      name: `${m.model_name} (${m.provider_name})`,
      key: `${m.provider_name}-${m.model_name}`,
      model_name: m.model_name,
      provider_name: m.provider_name,
      total_tokens: m.total_tokens,
      value: m.total_tokens,
      percentage: totalTokens > 0 ? (m.total_tokens / totalTokens) * 100 : 0,
    }));

  return (
    <div className="flex h-full flex-col justify-between rounded-xl border border-border-subtle bg-card p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <div className="rounded-md bg-accent-primary/10 p-1.5 text-accent-primary">
            <PieChartIcon className="h-4 w-4" aria-hidden="true" />
          </div>
          <h3 className="text-sm font-semibold tracking-tight text-text-primary">
            Part de Marché des Modèles (Donut)
          </h3>
        </div>
        <span className="font-mono text-xs text-text-secondary tabular-nums">
          {models.length} modèles au total
        </span>
      </div>

      {/* Donut Canvas */}
      <div className="my-2 h-52 w-full">
        {chartData.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-xs text-text-secondary">
            <p>En attente d&apos;inférences...</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Tooltip content={<CustomDonutTooltip />} />
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={4}
                stroke="#0D121F"
                strokeWidth={2}
              >
                {chartData.map((entry, index) => (
                  <Cell key={entry.key} fill={PALETTE[index % PALETTE.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Visual Legend Pills */}
      <div className="mt-2 flex flex-wrap items-center justify-center gap-2 border-t border-border-subtle/50 pt-3">
        {chartData.slice(0, 4).map((entry, index) => (
          <div
            key={entry.key}
            className="flex items-center gap-1.5 rounded-full border border-slate-700 bg-surface/80 px-2.5 py-1 text-[11px] font-mono tabular-nums"
          >
            <span
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: PALETTE[index % PALETTE.length] }}
            />
            <span
              className="max-w-[130px] truncate text-slate-200"
              title={`${entry.model_name} (${entry.provider_name})`}
            >
              {entry.model_name} <span className="text-[10px] text-slate-400">({entry.provider_name})</span>
            </span>
            <span className="font-semibold text-sky-400">{entry.percentage.toFixed(0)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
