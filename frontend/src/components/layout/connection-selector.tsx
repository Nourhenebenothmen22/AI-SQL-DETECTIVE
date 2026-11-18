"use client";

import { Database, Lock } from "lucide-react";

import { useConnection } from "@/components/providers/connection-provider";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export function ConnectionSelector() {
  const {
    connectionId,
    setConnectionId,
    connections,
    activeConnection,
    connectionsLoading,
  } = useConnection();

  if (connectionsLoading) {
    return <Skeleton className="h-8 w-64" />;
  }

  return (
    <div className="flex flex-wrap items-center gap-2.5">
      <div className="flex items-center gap-2 rounded-md border border-border-subtle bg-card px-2.5 py-1">
        <Database className="h-3.5 w-3.5 shrink-0 text-accent-primary" aria-hidden="true" />
        <label htmlFor="db-connection-select" className="sr-only">
          Database connection
        </label>
        <select
          id="db-connection-select"
          value={connectionId ?? ""}
          onChange={(event) => setConnectionId(event.target.value)}
          disabled={connections.length === 0}
          className="bg-transparent text-xs font-medium text-text-primary outline-none"
        >
          {connections.length === 0 ? (
            <option value="" className="bg-surface text-text-secondary">
              No connection available
            </option>
          ) : (
            connections.map((conn) => (
              <option key={conn.id} value={conn.id} className="bg-surface text-text-primary">
                {conn.display_name}
              </option>
            ))
          )}
        </select>
      </div>

      {activeConnection ? (
        <>
          <Badge variant="cyan">
            <Lock className="h-3 w-3" aria-hidden="true" />
            READ-ONLY
          </Badge>
          <span className="hidden font-mono text-[11px] tabular-nums text-text-secondary lg:inline">
            schema: {activeConnection.target_schemas.join(", ")} · limit {activeConnection.max_rows}
            {" · "}
            {activeConnection.statement_timeout_ms}ms timeout
          </span>
        </>
      ) : null}
    </div>
  );
}
