"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ChevronDown,
  ChevronRight,
  KeyRound,
  Link2,
  RefreshCw,
  Search,
  Table2,
} from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api-client";
import { formatBytes, formatNumber } from "@/lib/format";

interface SchemaExplorerProps {
  connectionId: string | undefined;
  onInsertIdentifier: (snippet: string) => void;
}

export function SchemaExplorer({ connectionId, onInsertIdentifier }: SchemaExplorerProps) {
  const [search, setSearch] = useState("");
  const [expandedTables, setExpandedTables] = useState<Record<string, boolean>>({
    "ecommerce.orders": true,
    "ecommerce.customers": true,
  });

  const schemaQuery = useQuery({
    queryKey: ["schema", connectionId],
    queryFn: ({ signal }) => apiClient.getSchema(connectionId, signal),
    enabled: Boolean(connectionId),
  });

  const filteredTables = useMemo(() => {
    const tables = schemaQuery.data?.tables ?? [];
    const term = search.trim().toLowerCase();
    if (!term) return tables;
    return tables.filter(
      (table) =>
        table.table_name.toLowerCase().includes(term) ||
        table.columns.some((col) => col.name.toLowerCase().includes(term)),
    );
  }, [schemaQuery.data?.tables, search]);

  const toggleTable = (fullName: string) => {
    setExpandedTables((prev) => ({ ...prev, [fullName]: !prev[fullName] }));
  };

  return (
    <section className="flex h-full flex-col rounded-lg border border-border-subtle bg-surface">
      <div className="flex items-center justify-between border-b border-border-subtle px-3.5 py-2.5">
        <div className="flex items-center gap-2">
          <Table2 className="h-4 w-4 text-accent-secondary" aria-hidden="true" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-text-primary">
            Schema Explorer
          </h2>
          {schemaQuery.data ? (
            <Badge variant="default">{schemaQuery.data.table_count}</Badge>
          ) : null}
        </div>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Refresh schema metadata"
          onClick={() => void schemaQuery.refetch()}
          disabled={schemaQuery.isFetching}
        >
          <RefreshCw
            className={`h-3.5 w-3.5 ${schemaQuery.isFetching ? "animate-spin" : ""}`}
            aria-hidden="true"
          />
        </Button>
      </div>

      <div className="border-b border-border-subtle p-2.5">
        <label htmlFor="schema-search-input" className="sr-only">
          Filter tables and columns
        </label>
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-secondary"
            aria-hidden="true"
          />
          <input
            id="schema-search-input"
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Filter tables or columns..."
            className="h-8 w-full rounded-md border border-border-subtle bg-canvas pl-8 pr-2.5 text-xs text-text-primary placeholder:text-text-secondary/70"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {schemaQuery.isLoading ? (
          <div className="space-y-2 p-1.5">
            {Array.from({ length: 7 }).map((_, idx) => (
              <Skeleton key={idx} className="h-8 w-full" />
            ))}
          </div>
        ) : schemaQuery.isError ? (
          <div
            role="alert"
            className="m-1.5 rounded-md border border-status-error/40 bg-status-error/10 p-3 text-xs text-text-primary"
          >
            <div className="flex items-center gap-1.5 font-medium text-status-error">
              <AlertCircle className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Schema unavailable</span>
            </div>
            <p className="mt-1 text-text-secondary">
              {schemaQuery.error instanceof Error
                ? schemaQuery.error.message
                : "Could not introspect target PostgreSQL schema."}
            </p>
            <Button
              variant="outline"
              size="sm"
              className="mt-2.5"
              onClick={() => void schemaQuery.refetch()}
            >
              Retry
            </Button>
          </div>
        ) : filteredTables.length === 0 ? (
          <p className="px-3 py-6 text-center text-xs text-text-secondary">
            No tables or columns match &ldquo;{search}&rdquo;.
          </p>
        ) : (
          <ul className="space-y-1">
            {filteredTables.map((table) => {
              const fullName = `${table.schema_name}.${table.table_name}`;
              const isOpen = Boolean(expandedTables[fullName]) || Boolean(search.trim());
              return (
                <li
                  key={fullName}
                  className="rounded-md border border-border-subtle/70 bg-card/60"
                >
                  <div className="flex items-center justify-between gap-1 px-2 py-1.5">
                    <button
                      type="button"
                      onClick={() => toggleTable(fullName)}
                      aria-expanded={isOpen}
                      className="flex min-w-0 flex-1 items-center gap-1.5 text-left"
                    >
                      {isOpen ? (
                        <ChevronDown
                          className="h-3.5 w-3.5 shrink-0 text-text-secondary"
                          aria-hidden="true"
                        />
                      ) : (
                        <ChevronRight
                          className="h-3.5 w-3.5 shrink-0 text-text-secondary"
                          aria-hidden="true"
                        />
                      )}
                      <span className="truncate font-mono text-xs font-medium text-text-primary">
                        {table.table_name}
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => onInsertIdentifier(fullName)}
                      aria-label={`Insert ${fullName} into SQL editor`}
                      className="shrink-0 rounded px-1.5 py-0.5 font-mono text-[10px] tabular-nums text-text-secondary transition-colors hover:bg-surface hover:text-accent-secondary"
                    >
                      ~{formatNumber(table.estimated_row_count)}
                    </button>
                  </div>

                  {isOpen ? (
                    <div className="border-t border-border-subtle/60 px-2.5 py-2">
                      <div className="mb-1.5 flex items-center justify-between font-mono text-[10px] text-text-secondary">
                        <span>{fullName}</span>
                        <span className="tabular-nums">
                          {formatBytes(table.total_size_bytes)} · {table.indexes.length} idx
                        </span>
                      </div>

                      <ul className="space-y-1">
                        {table.columns.map((col) => (
                          <li key={col.name}>
                            <button
                              type="button"
                              onClick={() => onInsertIdentifier(`${table.table_name}.${col.name}`)}
                              className="flex w-full items-center justify-between gap-2 rounded px-1.5 py-1 text-left transition-colors hover:bg-surface"
                            >
                              <span className="flex min-w-0 items-center gap-1.5 font-mono text-[11px] text-text-primary">
                                {col.is_primary_key ? (
                                  <KeyRound
                                    className="h-3 w-3 shrink-0 text-status-warning"
                                    aria-hidden="true"
                                  />
                                ) : col.is_foreign_key ? (
                                  <Link2
                                    className="h-3 w-3 shrink-0 text-accent-secondary"
                                    aria-hidden="true"
                                  />
                                ) : (
                                  <span className="inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-border-subtle" />
                                )}
                                <span className="truncate">{col.name}</span>
                              </span>
                              <span className="shrink-0 font-mono text-[10px] text-text-secondary">
                                {col.udt_name}
                              </span>
                            </button>
                          </li>
                        ))}
                      </ul>

                      {table.indexes.filter((idx) => !idx.is_primary).length > 0 ? (
                        <div className="mt-2 border-t border-border-subtle/50 pt-1.5">
                          <p className="font-mono text-[10px] uppercase tracking-wider text-text-secondary">
                            Indexes
                          </p>
                          <ul className="mt-1 space-y-0.5">
                            {table.indexes
                              .filter((idx) => !idx.is_primary)
                              .map((idx) => (
                                <li
                                  key={idx.name}
                                  className="truncate font-mono text-[10px] text-text-secondary"
                                >
                                  {idx.name} ({idx.columns.join(", ")})
                                </li>
                              ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
