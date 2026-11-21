"use client";

import { BarChart2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatNumber } from "@/lib/format";
import type { ModelUsageSummary } from "@/types/evallaps";

interface TokenIoChartProps {
  models: ModelUsageSummary[];
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey: string;
    payload: {
      model_label: string;
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
      input_cost: number;
      output_cost: number;
    };
  }>;
}

function CustomBarTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload.length) return null;
  const first = payload[0];
  if (!first) return null;
  const data = first.payload;

  return (
    <div className="rounded-lg border border-border-subtle bg-card p-3 shadow-xl font-mono text-xs">
      <p className="font-semibold text-text-primary">{data.model_label}</p>
      <div className="mt-2 space-y-1 text-[11px] tabular-nums">
        <div className="flex items-center justify-between gap-4 text-accent-primary">
          <span>Prompt (Input) :</span>
          <span>{formatNumber(data.prompt_tokens)}</span>
        </div>
        <div className="flex items-center justify-between gap-4 text-accent-secondary">
          <span>Completion (Output) :</span>
          <span>{formatNumber(data.completion_tokens)}</span>
        </div>
        <div className="flex items-center justify-between gap-4 border-t border-border-subtle/60 pt-1 font-bold text-text-primary">
          <span>Total :</span>
          <span>{formatNumber(data.total_tokens)}</span>
        </div>
      </div>
    </div>
  );
}

export function TokenIoChart({ models }: TokenIoChartProps) {
  const chartData = models
    .filter((m) => m.total_tokens > 0)
    .slice(0, 6)
    .map((m) => ({
      name: m.model_name.length > 14 ? `${m.model_name.slice(0, 12)}…` : m.model_name,
      model_label: m.model_name,
      prompt_tokens: m.prompt_tokens,
      completion_tokens: m.completion_tokens,
      total_tokens: m.total_tokens,
      input_cost: m.input_cost_usd,
      output_cost: m.output_cost_usd,
    }));

  return (
    <div className="flex h-full flex-col justify-between rounded-xl border border-border-subtle bg-card p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <div className="rounded-md bg-accent-secondary/10 p-1.5 text-accent-secondary">
            <BarChart2 className="h-4 w-4" aria-hidden="true" />
          </div>
          <h3 className="text-sm font-semibold tracking-tight text-text-primary">
            Ventilation Input vs Output (Prompts vs Génération)
          </h3>
        </div>
        <span className="font-mono text-xs text-text-secondary">Comparatif I/O</span>
      </div>

      {/* Bar Canvas */}
      <div className="my-2 h-52 w-full">
        {chartData.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-xs text-text-secondary">
            <p>En attente de télémétrie...</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1E2B45" vertical={false} />
              <XAxis
                dataKey="name"
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: "#1E2B45" }}
              />
              <YAxis
                stroke="#64748B"
                fontSize={11}
                tickLine={false}
                axisLine={{ stroke: "#1E2B45" }}
                tickFormatter={(val: number) => (val >= 1000 ? `${(val / 1000).toFixed(0)}k` : String(val))}
              />
              <Tooltip content={<CustomBarTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
                iconType="circle"
                iconSize={8}
              />
              <Bar dataKey="prompt_tokens" name="Prompt Tokens" fill="#6366F1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="completion_tokens" name="Completion Tokens" fill="#06B6D4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Footer summary */}
      <div className="mt-2 flex items-center justify-between border-t border-border-subtle/50 pt-3 text-[11px] font-mono text-text-secondary">
        <span>Barème standard $2.50 / $10.00 par Million</span>
        <span className="text-emerald-400 font-semibold">100% Épargné (Free Tier)</span>
      </div>
    </div>
  );
}
