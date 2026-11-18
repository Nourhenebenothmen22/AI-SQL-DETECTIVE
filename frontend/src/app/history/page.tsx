"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertCircle, ArrowUpRight, History, RefreshCw, Search } from "lucide-react";
import Link from "next/link";
import { useId, useState } from "react";

import { useConnection } from "@/components/providers/connection-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api-client";
import { formatDurationMs, formatNumber, formatTimestamp } from "@/lib/format";
import type { ExecutionStatus } from "@/types/api";

const PAGE_SIZE = 20;

export default function HistoryPage() {
  const { connectionId } = useConnection();
  const captionId = useId();
  const [search, setSearch] = useState("");
  const [mode, setMode] = useState<"all" | "nl" | "manual_sql">("all");
  const [securityStatus, setSecurityStatus] = useState<"all" | "passed" | "blocked">("all");
  const [executionStatus, setExecutionStatus] = useState<"all" | ExecutionStatus>("all");
  const [offset, setOffset] = useState(0);

  const historyQuery = useQuery({
    queryKey: ["history", connectionId, mode, securityStatus, executionStatus, search, offset],
    queryFn: ({ signal }) =>
      apiClient.getHistory(
        {
          connection_id: connectionId,
          mode: mode === "all" ? undefined : mode,
          security_status: securityStatus === "all" ? undefined : securityStatus,
          execution_status: executionStatus === "all" ? undefined : executionStatus,
          search: search.trim() || undefined,
          limit: PAGE_SIZE,
          offset,
        },
        signal,
      ),
  });

  const total = historyQuery.data?.total ?? 0;
  const items = historyQuery.data?.items ?? [];

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-5 p-4 lg:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold tracking-tight text-text-primary">Query History</h1>
          <p className="text-xs text-text-secondary">
            Auditable log of natural-language and manual SQL runs recorded in{" "}
            <code className="text-accent-secondary">app_meta.query_runs</code>.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => void historyQuery.refetch()}
          disabled={historyQuery.isFetching}
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${historyQuery.isFetching ? "animate-spin" : ""}`}
            aria-hidden="true"
          />
          <span>Refresh</span>
        </Button>
      </div>

      {/* Filters */}
      <div className="grid gap-3 rounded-lg border border-border-subtle bg-card p-3.5 md:grid-cols-4">
        <div>
          <label
            htmlFor="history-search"
            className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-text-secondary"
          >
            Search Prompt or SQL
          </label>
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-secondary"
              aria-hidden="true"
            />
            <input
              id="history-search"
              type="search"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setOffset(0);
              }}
              placeholder="Filter runs..."
              className="h-8 w-full rounded-md border border-border-subtle bg-canvas pl-8 pr-2.5 text-xs text-text-primary placeholder:text-text-secondary/70"
            />
          </div>
        </div>

        <div>
          <label
            htmlFor="history-mode"
            className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-text-secondary"
          >
            Mode
          </label>
          <select
            id="history-mode"
            value={mode}
            onChange={(event) => {
              setMode(event.target.value as "all" | "nl" | "manual_sql");
              setOffset(0);
            }}
            className="h-8 w-full rounded-md border border-border-subtle bg-canvas px-2.5 text-xs text-text-primary"
          >
            <option value="all">All modes</option>
            <option value="nl">Natural Language (AI)</option>
            <option value="manual_sql">Manual SQL</option>
          </select>
        </div>

        <div>
          <label
            htmlFor="history-security"
            className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-text-secondary"
          >
            Security Gate
          </label>
          <select
            id="history-security"
            value={securityStatus}
            onChange={(event) => {
              setSecurityStatus(event.target.value as "all" | "passed" | "blocked");
              setOffset(0);
            }}
            className="h-8 w-full rounded-md border border-border-subtle bg-canvas px-2.5 text-xs text-text-primary"
          >
            <option value="all">All verdicts</option>
            <option value="passed">Passed</option>
            <option value="blocked">Blocked</option>
          </select>
        </div>

        <div>
          <label
            htmlFor="history-exec"
            className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-text-secondary"
          >
            Execution Status
          </label>
          <select
            id="history-exec"
            value={executionStatus}
            onChange={(event) => {
              setExecutionStatus(event.target.value as "all" | ExecutionStatus);
              setOffset(0);
            }}
            className="h-8 w-full rounded-md border border-border-subtle bg-canvas px-2.5 text-xs text-text-primary"
          >
            <option value="all">All statuses</option>
            <option value="success">Success</option>
            <option value="error">Error</option>
            <option value="timeout">Timeout</option>
            <option value="skipped">Skipped</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {historyQuery.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, idx) => (
            <Skeleton key={idx} className="h-12 w-full" />
          ))}
        </div>
      ) : historyQuery.isError ? (
        <div
          role="alert"
          className="rounded-lg border border-status-error/40 bg-status-error/10 p-5 text-xs"
        >
          <div className="flex items-center gap-2 font-semibold text-status-error">
            <AlertCircle className="h-4 w-4" aria-hidden="true" />
            <span>Unable to load query history</span>
          </div>
          <p className="mt-1 text-text-secondary">
            {historyQuery.error instanceof Error
              ? historyQuery.error.message
              : "Telemetry database is unavailable."}
          </p>
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border-subtle bg-card px-6 py-12 text-center">
          <History className="h-7 w-7 text-text-secondary/60" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium text-text-primary">No matching query runs</p>
          <p className="mt-1 text-xs text-text-secondary">
            Run a query in the Workbench or relax your filters to inspect historical runs.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <div
            tabIndex={0}
            role="region"
            aria-labelledby={captionId}
            className="overflow-x-auto rounded-lg border border-border-subtle bg-card"
          >
            <table className="w-full min-w-[780px] border-separate border-spacing-0 text-left text-xs">
              <caption id={captionId} className="sr-only">
                Query run history ({total} total runs)
              </caption>
              <thead className="bg-surface">
                <tr className="font-mono text-[11px] text-text-secondary">
                  <th scope="col" className="border-b border-border-subtle px-3 py-2.5">
                    Timestamp
                  </th>
                  <th scope="col" className="border-b border-border-subtle px-3 py-2.5">
                    Mode
                  </th>
                  <th scope="col" className="border-b border-border-subtle px-3 py-2.5">
                    Question / SQL
                  </th>
                  <th scope="col" className="border-b border-border-subtle px-3 py-2.5">
                    Security
                  </th>
                  <th scope="col" className="border-b border-border-subtle px-3 py-2.5">
                    Execution
                  </th>
                  <th scope="col" className="border-b border-border-subtle px-3 py-2.5 text-right">
                    Rows
                  </th>
                  <th scope="col" className="border-b border-border-subtle px-3 py-2.5 text-right">
                    Latency
                  </th>
                  <th scope="col" className="border-b border-border-subtle px-3 py-2.5 text-right">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((run) => (
                  <tr key={run.id} className="transition-colors hover:bg-surface/70">
                    <td className="whitespace-nowrap border-b border-border-subtle/50 px-3 py-2.5 font-mono text-[11px] tabular-nums text-text-secondary">
                      {formatTimestamp(run.created_at)}
                    </td>
                    <td className="border-b border-border-subtle/50 px-3 py-2.5">
                      <Badge variant={run.mode === "nl" ? "indigo" : "default"}>
                        {run.mode === "nl" ? "AI NL" : "SQL"}
                      </Badge>
                    </td>
                    <td className="max-w-md border-b border-border-subtle/50 px-3 py-2.5">
                      {run.natural_language_prompt ? (
                        <p className="truncate font-medium text-text-primary">
                          {run.natural_language_prompt}
                        </p>
                      ) : null}
                      <p className="truncate font-mono text-[11px] text-text-secondary">
                        {run.validated_sql ?? run.generated_sql ?? "—"}
                      </p>
                    </td>
                    <td className="border-b border-border-subtle/50 px-3 py-2.5">
                      <Badge variant={run.security_status === "passed" ? "success" : "error"}>
                        {run.security_status}
                      </Badge>
                    </td>
                    <td className="border-b border-border-subtle/50 px-3 py-2.5">
                      <Badge
                        variant={
                          run.execution_status === "success"
                            ? "success"
                            : run.execution_status === "skipped"
                              ? "default"
                              : run.execution_status === "timeout" ||
                                  run.execution_status === "cancelled"
                                ? "warning"
                                : "error"
                        }
                      >
                        {run.execution_status}
                      </Badge>
                    </td>
                    <td className="border-b border-border-subtle/50 px-3 py-2.5 text-right font-mono tabular-nums text-text-primary">
                      {formatNumber(run.row_count)}
                    </td>
                    <td className="border-b border-border-subtle/50 px-3 py-2.5 text-right font-mono tabular-nums text-accent-secondary">
                      {formatDurationMs(run.execution_time_ms)}
                    </td>
                    <td className="border-b border-border-subtle/50 px-3 py-2.5 text-right">
                      <Link
                        href={`/?runId=${encodeURIComponent(run.id)}`}
                        aria-label={`Open run ${run.id} in Workbench`}
                        className="inline-flex items-center gap-1 rounded border border-border-subtle bg-surface px-2 py-1 text-[11px] font-medium text-text-primary transition-colors hover:border-accent-primary/60 hover:text-accent-secondary"
                      >
                        <span>Open</span>
                        <ArrowUpRight className="h-3 w-3" aria-hidden="true" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-xs text-text-secondary">
            <span className="font-mono tabular-nums">
              Showing {offset + 1}–{Math.min(offset + items.length, total)} of{" "}
              {formatNumber(total)}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset((prev) => Math.max(0, prev - PAGE_SIZE))}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => setOffset((prev) => prev + PAGE_SIZE)}
              >
                Next
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
