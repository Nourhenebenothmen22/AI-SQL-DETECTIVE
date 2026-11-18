"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { formatBytes, formatNumber } from "@/lib/format";
import type { AnalyticsDashboardResponse } from "@/types/api";

const COLORS = {
  indigo: "#6366F1",
  cyan: "#22D3EE",
  emerald: "#10B981",
  amber: "#F59E0B",
  rose: "#F43F5E",
  border: "#263449",
  axis: "#94A3B8",
  card: "#172033",
  text: "#F8FAFC",
} as const;

const STATUS_COLORS: Record<string, string> = {
  passed: COLORS.emerald,
  optimized: COLORS.cyan,
  blocked: COLORS.amber,
  failed: COLORS.rose,
};

const TOOLTIP_STYLE = {
  backgroundColor: COLORS.card,
  border: `1px solid ${COLORS.border}`,
  borderRadius: "6px",
  color: COLORS.text,
  fontSize: "12px",
  fontFamily: "var(--font-jetbrains-mono), monospace",
};

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="flex h-60 items-center justify-center rounded-md border border-dashed border-border-subtle bg-surface/50 px-4 text-center text-xs text-text-secondary">
      {message}
    </div>
  );
}

export function AnalyticsCharts({ data }: { data: AnalyticsDashboardResponse }) {
  const nonZeroStatuses = data.status_distribution.filter((item) => item.count > 0);

  return (
    <div className="grid gap-5 lg:grid-cols-2">
      {/* 1. Line Chart: Execution Latency Trends */}
      <figure className="rounded-lg border border-border-subtle bg-card p-4">
        <figcaption className="mb-3">
          <h2 className="text-sm font-semibold text-text-primary">Execution Latency Trends</h2>
          <p className="text-xs text-text-secondary">
            Daily average and peak SQL execution time in milliseconds.
          </p>
        </figcaption>
        {data.execution_trends.length === 0 ? (
          <EmptyChart message="Run queries in the Workbench to populate execution latency trends." />
        ) : (
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.execution_trends}>
                <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke={COLORS.axis} fontSize={11} />
                <YAxis stroke={COLORS.axis} fontSize={11} unit="ms" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
                <Line
                  type="monotone"
                  dataKey="avg_execution_time_ms"
                  name="Avg Latency (ms)"
                  stroke={COLORS.indigo}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
                <Line
                  type="monotone"
                  dataKey="max_execution_time_ms"
                  name="Peak Latency (ms)"
                  stroke={COLORS.cyan}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </figure>

      {/* 2. Donut Chart: Query Status Distribution */}
      <figure className="rounded-lg border border-border-subtle bg-card p-4">
        <figcaption className="mb-3">
          <h2 className="text-sm font-semibold text-text-primary">Query Status Distribution</h2>
          <p className="text-xs text-text-secondary">
            Breakdown of passed, optimized, security-blocked, and failed/cancelled runs.
          </p>
        </figcaption>
        {nonZeroStatuses.length === 0 ? (
          <EmptyChart message="No query runs recorded in this window yet." />
        ) : (
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={nonZeroStatuses}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  innerRadius={56}
                  outerRadius={86}
                  paddingAngle={2}
                >
                  {nonZeroStatuses.map((entry) => (
                    <Cell
                      key={entry.status}
                      fill={STATUS_COLORS[entry.status] ?? COLORS.indigo}
                    />
                  ))}
                </Pie>
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </figure>

      {/* 3. Area Chart: Query Activity Over Time */}
      <figure className="rounded-lg border border-border-subtle bg-card p-4">
        <figcaption className="mb-3">
          <h2 className="text-sm font-semibold text-text-primary">Query Activity Over Time</h2>
          <p className="text-xs text-text-secondary">
            Daily query volume split between Natural Language (AI) and Manual SQL runs.
          </p>
        </figcaption>
        {data.activity_over_time.length === 0 ? (
          <EmptyChart message="No activity buckets available yet." />
        ) : (
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.activity_over_time}>
                <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke={COLORS.axis} fontSize={11} />
                <YAxis stroke={COLORS.axis} fontSize={11} allowDecimals={false} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
                <Area
                  type="monotone"
                  dataKey="nl_count"
                  name="Natural Language"
                  stackId="1"
                  stroke={COLORS.indigo}
                  fill={COLORS.indigo}
                  fillOpacity={0.28}
                />
                <Area
                  type="monotone"
                  dataKey="manual_sql_count"
                  name="Manual SQL"
                  stackId="1"
                  stroke={COLORS.cyan}
                  fill={COLORS.cyan}
                  fillOpacity={0.24}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </figure>

      {/* 4. Bar Chart: Recent Query Comparisons */}
      <figure className="rounded-lg border border-border-subtle bg-card p-4">
        <figcaption className="mb-3">
          <h2 className="text-sm font-semibold text-text-primary">Recent Query Comparisons</h2>
          <p className="text-xs text-text-secondary">
            Execution time (ms) across the most recent successful read-only queries.
          </p>
        </figcaption>
        {data.query_comparisons.length === 0 ? (
          <EmptyChart message="Execute read-only queries to compare latencies side by side." />
        ) : (
          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.query_comparisons}>
                <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                <XAxis
                  dataKey="label"
                  stroke={COLORS.axis}
                  fontSize={10}
                  tickFormatter={(v: string) => (v.length > 14 ? `${v.slice(0, 14)}…` : v)}
                />
                <YAxis stroke={COLORS.axis} fontSize={11} unit="ms" />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Bar
                  dataKey="execution_time_ms"
                  name="Execution Time (ms)"
                  fill={COLORS.indigo}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </figure>

      {/* 5. Horizontal Bar Chart: Database Table Statistics */}
      <figure className="rounded-lg border border-border-subtle bg-card p-4 lg:col-span-2">
        <figcaption className="mb-3">
          <h2 className="text-sm font-semibold text-text-primary">
            PostgreSQL Table Statistics ({data.connection_id})
          </h2>
          <p className="text-xs text-text-secondary">
            Estimated live row counts from PostgreSQL system catalogs across introspected tables.
          </p>
        </figcaption>
        {data.database_statistics.length === 0 ? (
          <EmptyChart message="Database table statistics are currently unavailable." />
        ) : (
          <div className="grid gap-4 xl:grid-cols-3">
            <div className="h-72 w-full xl:col-span-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={data.database_statistics}
                  layout="vertical"
                  margin={{ left: 24, right: 20 }}
                >
                  <CartesianGrid stroke={COLORS.border} strokeDasharray="3 3" />
                  <XAxis type="number" stroke={COLORS.axis} fontSize={11} />
                  <YAxis
                    type="category"
                    dataKey="table_name"
                    stroke={COLORS.axis}
                    fontSize={11}
                    width={100}
                  />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar
                    dataKey="estimated_row_count"
                    name="Estimated Rows"
                    fill={COLORS.cyan}
                    radius={[0, 4, 4, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="overflow-auto rounded-md border border-border-subtle bg-surface">
              <table className="w-full border-collapse text-left text-xs">
                <caption className="sr-only">Table storage sizes and index counts</caption>
                <thead>
                  <tr className="border-b border-border-subtle text-text-secondary">
                    <th scope="col" className="px-3 py-2 font-mono text-[11px]">
                      Table
                    </th>
                    <th scope="col" className="px-3 py-2 text-right font-mono text-[11px]">
                      Rows
                    </th>
                    <th scope="col" className="px-3 py-2 text-right font-mono text-[11px]">
                      Size
                    </th>
                    <th scope="col" className="px-3 py-2 text-right font-mono text-[11px]">
                      Idx
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.database_statistics.map((stat) => (
                    <tr key={stat.table_name} className="border-b border-border-subtle/50">
                      <td className="px-3 py-1.5 font-mono text-text-primary">{stat.table_name}</td>
                      <td className="px-3 py-1.5 text-right font-mono tabular-nums text-accent-secondary">
                        {formatNumber(stat.estimated_row_count)}
                      </td>
                      <td className="px-3 py-1.5 text-right font-mono tabular-nums text-text-secondary">
                        {formatBytes(stat.total_size_bytes)}
                      </td>
                      <td className="px-3 py-1.5 text-right font-mono tabular-nums text-text-secondary">
                        {stat.index_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </figure>
    </div>
  );
}
