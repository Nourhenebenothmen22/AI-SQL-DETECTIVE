"use client";

import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Download,
  Search,
  TableProperties,
} from "lucide-react";
import { useId, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { exportRowsToCsv, formatDurationMs, formatNumber } from "@/lib/format";
import { cn } from "@/lib/utils";

const TEXT_COLLATOR = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

interface ResultsTableProps {
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  wasTruncated: boolean;
  enforcedLimit: number | null;
  executionTimeMs: number | null;
  executionError: string | null;
  isLoading: boolean;
}

type SortDirection = "ascending" | "descending";

function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return "NULL";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function ResultsTable({
  columns,
  rows,
  rowCount,
  wasTruncated,
  enforcedLimit,
  executionTimeMs,
  executionError,
  isLoading,
}: ResultsTableProps) {
  const captionId = useId();
  const filterId = useId();
  const [filterText, setFilterText] = useState("");
  const [sortCol, setSortCol] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<SortDirection>("ascending");
  const [announcement, setAnnouncement] = useState("");

  const filteredAndSortedRows = useMemo(() => {
    const query = filterText.trim().toLowerCase();
    const filtered = query
      ? rows.filter((row) =>
          columns.some((col) => formatCellValue(row[col]).toLowerCase().includes(query)),
        )
      : rows;

    if (!sortCol || !columns.includes(sortCol)) {
      return filtered;
    }

    const factor = sortDir === "ascending" ? 1 : -1;
    return [...filtered].sort((a, b) => {
      const av = a[sortCol];
      const bv = b[sortCol];
      if (av === null || av === undefined) return bv === null || bv === undefined ? 0 : 1;
      if (bv === null || bv === undefined) return -1;
      if (typeof av === "number" && typeof bv === "number") {
        return factor * (av - bv);
      }
      return factor * TEXT_COLLATOR.compare(formatCellValue(av), formatCellValue(bv));
    });
  }, [columns, filterText, rows, sortCol, sortDir]);

  const handleSort = (column: string) => {
    const nextDir: SortDirection =
      sortCol === column && sortDir === "ascending" ? "descending" : "ascending";
    setSortCol(column);
    setSortDir(nextDir);
    setAnnouncement(
      `Sorted by ${column}, ${nextDir}, ${filteredAndSortedRows.length} rows`,
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-2 rounded-lg border border-border-subtle bg-card p-4">
        <div className="h-4 w-48 animate-pulse rounded bg-border-subtle/50" />
        <div className="h-32 w-full animate-pulse rounded bg-border-subtle/40" />
      </div>
    );
  }

  if (executionError) {
    return (
      <div
        role="alert"
        className="rounded-lg border border-status-error/40 bg-status-error/10 p-4 text-xs"
      >
        <p className="font-semibold text-status-error">Query Execution Error</p>
        <p className="mt-1 font-mono text-text-primary">{executionError}</p>
      </div>
    );
  }

  if (columns.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-lg border border-border-subtle bg-card px-6 py-12 text-center">
        <TableProperties className="h-7 w-7 text-text-secondary/60" aria-hidden="true" />
        <p className="mt-3 text-sm font-medium text-text-primary">No results yet</p>
        <p className="mt-1 max-w-md text-xs text-text-secondary">
          Ask a natural-language question above or run a read-only PostgreSQL query in the editor to
          inspect rows here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2 font-mono text-xs tabular-nums">
          <Badge variant="default">{formatNumber(rowCount)} rows</Badge>
          <Badge variant="default">{columns.length} cols</Badge>
          {executionTimeMs !== null ? (
            <Badge variant="cyan">{formatDurationMs(executionTimeMs)}</Badge>
          ) : null}
          {wasTruncated && enforcedLimit ? (
            <Badge variant="warning">
              <AlertTriangle className="h-3 w-3" aria-hidden="true" />
              Truncated at LIMIT {enforcedLimit}
            </Badge>
          ) : null}
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor={filterId} className="sr-only">
            Filter returned rows
          </label>
          <div className="relative">
            <Search
              className="pointer-events-none absolute left-2.5 top-2 h-3.5 w-3.5 text-text-secondary"
              aria-hidden="true"
            />
            <input
              id={filterId}
              type="search"
              value={filterText}
              onChange={(event) => setFilterText(event.target.value)}
              placeholder="Filter rows..."
              className="h-8 w-44 rounded-md border border-border-subtle bg-canvas pl-8 pr-2.5 text-xs text-text-primary placeholder:text-text-secondary/70"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportRowsToCsv(columns, filteredAndSortedRows)}
            disabled={filteredAndSortedRows.length === 0}
          >
            <Download className="h-3.5 w-3.5" aria-hidden="true" />
            <span>Export CSV</span>
          </Button>
        </div>
      </div>

      <div
        tabIndex={0}
        role="region"
        aria-labelledby={captionId}
        className="max-h-96 overflow-auto rounded-lg border border-border-subtle bg-card"
      >
        <table className="w-full min-w-[600px] border-separate border-spacing-0 text-left text-xs">
          <caption id={captionId} className="sr-only">
            PostgreSQL query results table ({filteredAndSortedRows.length} rows)
          </caption>
          <thead className="sticky top-0 z-10 bg-surface">
            <tr>
              {columns.map((col) => {
                const isSorted = sortCol === col;
                return (
                  <th
                    key={col}
                    scope="col"
                    aria-sort={isSorted ? sortDir : undefined}
                    className="border-b border-border-subtle p-0 font-mono text-[11px] font-semibold text-text-secondary"
                  >
                    <button
                      type="button"
                      onClick={() => handleSort(col)}
                      className="flex min-h-9 w-full items-center justify-between gap-2 px-3 py-2 text-left transition-colors hover:bg-card hover:text-text-primary"
                    >
                      <span className="truncate">{col}</span>
                      {isSorted ? (
                        sortDir === "ascending" ? (
                          <ArrowUp
                            className="h-3 w-3 shrink-0 text-accent-primary"
                            aria-hidden="true"
                          />
                        ) : (
                          <ArrowDown
                            className="h-3 w-3 shrink-0 text-accent-primary"
                            aria-hidden="true"
                          />
                        )
                      ) : (
                        <ArrowUpDown
                          className="h-3 w-3 shrink-0 opacity-40"
                          aria-hidden="true"
                        />
                      )}
                    </button>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedRows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-xs text-text-secondary"
                >
                  {rows.length === 0
                    ? "Query succeeded and returned 0 rows."
                    : `No rows match filter "${filterText}".`}
                </td>
              </tr>
            ) : (
              filteredAndSortedRows.map((row, rowIdx) => (
                <tr
                  key={rowIdx}
                  className="transition-colors duration-100 hover:bg-surface/70"
                >
                  {columns.map((col) => {
                    const value = row[col];
                    const isNull = value === null || value === undefined;
                    const isNumeric = typeof value === "number";
                    return (
                      <td
                        key={col}
                        className={cn(
                          "max-w-xs truncate border-b border-border-subtle/50 px-3 py-2 font-mono text-xs",
                          isNumeric && "text-right tabular-nums text-accent-secondary",
                          !isNumeric && !isNull && "text-text-primary",
                        )}
                      >
                        {isNull ? (
                          <span className="rounded bg-surface px-1.5 py-0.5 text-[10px] text-text-secondary/70">
                            NULL
                          </span>
                        ) : (
                          formatCellValue(value)
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Single live status announcer for keyboard/screen-reader sort feedback */}
      <div role="status" className="sr-only">
        {announcement}
      </div>
    </div>
  );
}
