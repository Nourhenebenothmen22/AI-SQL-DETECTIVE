"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, AlertCircle, Gauge, RefreshCw, ShieldAlert, Zap } from "lucide-react";
import { useState } from "react";

import { AnalyticsCharts } from "@/components/charts/analytics-charts";
import { useConnection } from "@/components/providers/connection-provider";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api-client";
import { formatDurationMs, formatNumber } from "@/lib/format";

const WINDOW_OPTIONS = [7, 14, 30] as const;

export default function AnalyticsPage() {
  const { connectionId } = useConnection();
  const [days, setDays] = useState<number>(14);

  const analyticsQuery = useQuery({
    queryKey: ["analytics", connectionId, days],
    queryFn: ({ signal }) => apiClient.getAnalytics(connectionId, days, signal),
    enabled: Boolean(connectionId),
  });

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-5 p-4 lg:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-text-primary">
            Query &amp; Database Analytics
          </h1>
          <p className="text-xs text-text-secondary">
            Live telemetry aggregated from <code className="text-accent-secondary">app_meta</code>{" "}
            combined with PostgreSQL catalog statistics from the active read-only connection.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div
            role="group"
            aria-label="Analytics time window"
            className="inline-flex rounded-md border border-border-subtle bg-surface p-0.5"
          >
            {WINDOW_OPTIONS.map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={days === option}
                onClick={() => setDays(option)}
                className={`min-h-7 rounded px-2.5 font-mono text-xs transition-colors ${
                  days === option
                    ? "bg-card text-text-primary"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {option}d
              </button>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => void analyticsQuery.refetch()}
            disabled={analyticsQuery.isFetching}
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${analyticsQuery.isFetching ? "animate-spin" : ""}`}
              aria-hidden="true"
            />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {analyticsQuery.isLoading ? (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, idx) => (
              <Skeleton key={idx} className="h-24 w-full" />
            ))}
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            {Array.from({ length: 4 }).map((_, idx) => (
              <Skeleton key={idx} className="h-72 w-full" />
            ))}
          </div>
        </div>
      ) : analyticsQuery.isError ? (
        <div
          role="alert"
          className="rounded-lg border border-status-error/40 bg-status-error/10 p-5 text-sm"
        >
          <div className="flex items-center gap-2 font-semibold text-status-error">
            <AlertCircle className="h-4 w-4" aria-hidden="true" />
            <span>Unable to load analytics</span>
          </div>
          <p className="mt-1 text-xs text-text-secondary">
            {analyticsQuery.error instanceof Error
              ? analyticsQuery.error.message
              : "Backend analytics service is unavailable."}
          </p>
          <Button
            variant="outline"
            size="sm"
            className="mt-3"
            onClick={() => void analyticsQuery.refetch()}
          >
            Retry
          </Button>
        </div>
      ) : analyticsQuery.data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-border-subtle bg-card p-4">
              <div className="flex items-center justify-between text-xs text-text-secondary">
                <span>Total Query Runs</span>
                <Activity className="h-4 w-4 text-accent-primary" aria-hidden="true" />
              </div>
              <p className="mt-2 font-mono text-2xl font-semibold tabular-nums text-text-primary">
                {formatNumber(analyticsQuery.data.summary.total_runs)}
              </p>
              <p className="mt-1 font-mono text-[11px] tabular-nums text-text-secondary">
                {formatNumber(analyticsQuery.data.summary.passed_runs)} succeeded
              </p>
            </div>

            <div className="rounded-lg border border-border-subtle bg-card p-4">
              <div className="flex items-center justify-between text-xs text-text-secondary">
                <span>Blocked by Security Gate</span>
                <ShieldAlert className="h-4 w-4 text-status-warning" aria-hidden="true" />
              </div>
              <p className="mt-2 font-mono text-2xl font-semibold tabular-nums text-status-warning">
                {formatNumber(analyticsQuery.data.summary.blocked_runs)}
              </p>
              <p className="mt-1 font-mono text-[11px] tabular-nums text-text-secondary">
                {formatNumber(analyticsQuery.data.summary.failed_runs)} error/timeout ·{" "}
                {formatNumber(analyticsQuery.data.summary.cancelled_runs)} cancelled
              </p>
            </div>

            <div className="rounded-lg border border-border-subtle bg-card p-4">
              <div className="flex items-center justify-between text-xs text-text-secondary">
                <span>Average Latency</span>
                <Zap className="h-4 w-4 text-accent-secondary" aria-hidden="true" />
              </div>
              <p className="mt-2 font-mono text-2xl font-semibold tabular-nums text-accent-secondary">
                {formatDurationMs(analyticsQuery.data.summary.avg_execution_time_ms)}
              </p>
              <p className="mt-1 font-mono text-[11px] tabular-nums text-text-secondary">
                P95: {formatDurationMs(analyticsQuery.data.summary.p95_execution_time_ms)}
              </p>
            </div>

            <div className="rounded-lg border border-border-subtle bg-card p-4">
              <div className="flex items-center justify-between text-xs text-text-secondary">
                <span>Plans With Optimizations</span>
                <Gauge className="h-4 w-4 text-status-success" aria-hidden="true" />
              </div>
              <p className="mt-2 font-mono text-2xl font-semibold tabular-nums text-status-success">
                {formatNumber(analyticsQuery.data.summary.optimized_runs)}
              </p>
              <p className="mt-1 font-mono text-[11px] text-text-secondary">
                EXPLAIN (FORMAT JSON) analyzed
              </p>
            </div>
          </div>

          <AnalyticsCharts data={analyticsQuery.data} />
        </>
      ) : null}
    </div>
  );
}
