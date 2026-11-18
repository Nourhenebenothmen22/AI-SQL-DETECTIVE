"use client";

import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

import { apiClient } from "@/lib/api-client";
import type { ConnectionSummary, HealthResponse } from "@/types/api";

interface ConnectionContextValue {
  connectionId: string | undefined;
  setConnectionId: (id: string) => void;
  connections: ConnectionSummary[];
  activeConnection: ConnectionSummary | undefined;
  connectionsLoading: boolean;
  connectionsError: string | null;
  health: HealthResponse | undefined;
  healthLoading: boolean;
  refetchConnections: () => void;
}

const ConnectionContext = createContext<ConnectionContextValue | null>(null);

export function ConnectionProvider({ children }: { readonly children: ReactNode }) {
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);

  const connectionsQuery = useQuery({
    queryKey: ["connections"],
    queryFn: ({ signal }) => apiClient.getConnections(signal),
  });

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => apiClient.getHealth(signal),
    refetchInterval: 30_000,
  });

  const value = useMemo<ConnectionContextValue>(() => {
    const connections = connectionsQuery.data?.connections ?? [];
    const resolvedId =
      selectedId && connections.some((c) => c.id === selectedId)
        ? selectedId
        : (connectionsQuery.data?.default_connection_id ?? connections[0]?.id);
    const activeConnection = connections.find((c) => c.id === resolvedId);

    return {
      connectionId: resolvedId,
      setConnectionId: setSelectedId,
      connections,
      activeConnection,
      connectionsLoading: connectionsQuery.isLoading,
      connectionsError: connectionsQuery.error
        ? connectionsQuery.error instanceof Error
          ? connectionsQuery.error.message
          : "Unable to load configured connections."
        : null,
      health: healthQuery.data,
      healthLoading: healthQuery.isLoading,
      refetchConnections: () => {
        void connectionsQuery.refetch();
      },
    };
  }, [
    selectedId,
    connectionsQuery,
    healthQuery.data,
    healthQuery.isLoading,
  ]);

  return <ConnectionContext.Provider value={value}>{children}</ConnectionContext.Provider>;
}

export function useConnection(): ConnectionContextValue {
  const ctx = useContext(ConnectionContext);
  if (!ctx) {
    throw new Error("useConnection must be used within a ConnectionProvider.");
  }
  return ctx;
}
