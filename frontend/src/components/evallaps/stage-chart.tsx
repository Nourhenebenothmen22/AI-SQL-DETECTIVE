"use client";

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

import { formatCurrencyUsd, formatDurationMs, formatNumber } from "@/lib/format";
import type { StageUsageSummary } from "@/types/evallaps";

const CHART_COLORS = {
  prompt: "#38BDF8", // Sky Blue - High contrast & soothing
  completion: "#34D399", // Mint Green - High contrast & comfortable
  border: "#334155", // Slate-700
  axis: "#94A3B8", // Slate-400
  card: "#0F172A", // Slate-900
  text: "#F8FAFC",
};

const TOOLTIP_STYLE = {
  backgroundColor: CHART_COLORS.card,
  border: `1px solid ${CHART_COLORS.border}`,
  borderRadius: "6px",
  color: CHART_COLORS.text,
  fontSize: "12px",
  fontFamily: "var(--font-jetbrains-mono), monospace",
  boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
  padding: "8px 12px",
};

export function StageChart({ stages }: { stages: StageUsageSummary[] }) {
  if (stages.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-border-subtle bg-surface/40 text-xs text-text-secondary">
        Aucune donnée télémétrique d&apos;agent enregistrée pour cette période.
      </div>
    );
  }

  const chartData = stages.map((s) => ({
    name: s.stage_label.replace("Agent ", "A"),
    fullName: s.stage_label,
    stage_id: s.stage_id,
    prompt: s.prompt_tokens,
    completion: s.completion_tokens,
    total: s.total_tokens,
    savings: s.estimated_savings_usd,
    calls: s.total_calls,
    latency: s.avg_latency_ms,
  }));

  return (
    <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border-subtle pb-3">
        <div>
          <h2 className="text-sm font-semibold tracking-tight text-text-primary">
            Consommation de Tokens par Agent LLM
          </h2>
          <p className="text-xs text-text-secondary">
            Ventilation Prompt Tokens (Prompt) vs Completion Tokens (Réponse) pour chaque agent cognitif.
          </p>
        </div>
      </div>

      <div className="mt-4 h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" strokeOpacity={0.6} vertical={false} />
            <XAxis
              dataKey="name"
              stroke={CHART_COLORS.axis}
              fontSize={11}
              tickLine={false}
              interval={0}
              angle={-15}
              textAnchor="end"
            />
            <YAxis
              stroke={CHART_COLORS.axis}
              fontSize={11}
              tickLine={false}
              tickFormatter={(val: number) => (val >= 1000 ? `${(val / 1000).toFixed(1)}k` : String(val))}
            />
            <Tooltip
              contentStyle={TOOLTIP_STYLE}
              formatter={(value: unknown, name: unknown) => [
                formatNumber(Number(value)),
                name === "prompt" ? "Prompt Tokens" : "Completion Tokens",
              ]}
              labelFormatter={(_label, payload) => {
                if (!payload || payload.length === 0 || !payload[0]) return "";
                const item = payload[0].payload as {
                  fullName: string;
                  calls: number;
                  latency: number;
                  savings: number;
                };
                return `${item.fullName} (${item.calls} appel(s) · ${formatDurationMs(item.latency)} · ${formatCurrencyUsd(item.savings)} économisés)`;
              }}
            />
            <Legend
              verticalAlign="top"
              align="right"
              iconType="circle"
              wrapperStyle={{ fontSize: "11px", paddingBottom: "10px" }}
              formatter={(val) => (val === "prompt" ? "Prompt Tokens" : "Completion Tokens")}
            />
            <Bar dataKey="prompt" fill={CHART_COLORS.prompt} radius={[0, 0, 0, 0]} stackId="tokens" />
            <Bar dataKey="completion" fill={CHART_COLORS.completion} radius={[4, 4, 0, 0]} stackId="tokens" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
