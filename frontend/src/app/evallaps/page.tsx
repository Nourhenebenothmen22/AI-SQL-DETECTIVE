"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertCircle, Gauge, RefreshCw } from "lucide-react";
import { useState } from "react";

import { LoadBalancerVisual } from "@/components/evallaps/load-balancer-visual";
import { ModelDistributionChart } from "@/components/evallaps/model-distribution-chart";
import { ProviderCards } from "@/components/evallaps/provider-cards";
import { QuotaHero } from "@/components/evallaps/quota-hero";
import { StageChart } from "@/components/evallaps/stage-chart";
import { TokenBurnChart } from "@/components/evallaps/token-burn-chart";
import { TokenIoChart } from "@/components/evallaps/token-io-chart";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiClient } from "@/lib/api-client";

const WINDOW_OPTIONS = [7, 14, 30, 90] as const;

export default function EvalLapsPage() {
  const [days, setDays] = useState<number>(30);

  const summaryQuery = useQuery({
    queryKey: ["evallaps-summary", days],
    queryFn: ({ signal }) => apiClient.getEvalLapsSummary(days, signal),
  });

  const providersQuery = useQuery({
    queryKey: ["evallaps-providers", days],
    queryFn: ({ signal }) => apiClient.getEvalLapsProviders(days, signal),
  });

  const stagesQuery = useQuery({
    queryKey: ["evallaps-stages", days],
    queryFn: ({ signal }) => apiClient.getEvalLapsStages(days, signal),
  });

  const renewalsQuery = useQuery({
    queryKey: ["evallaps-renewals"],
    queryFn: ({ signal }) => apiClient.getEvalLapsRenewals(signal),
  });

  const cbQuery = useQuery({
    queryKey: ["evallaps-circuit-breaker"],
    queryFn: ({ signal }) => apiClient.getEvalLapsCircuitBreaker(signal),
    refetchInterval: 5000,
  });

  const modelsQuery = useQuery({
    queryKey: ["evallaps-models", days],
    queryFn: ({ signal }) => apiClient.getEvalLapsModels(days, signal),
  });

  const balanceQuery = useQuery({
    queryKey: ["evallaps-balance"],
    queryFn: ({ signal }) => apiClient.getEvalLapsLoadBalancer(signal),
    refetchInterval: 5000,
  });

  const overviewQuery = useQuery({
    queryKey: ["evallaps-overview"],
    queryFn: ({ signal }) => apiClient.getQuotaOverview(signal),
    refetchInterval: 5000,
  });

  const isLoading =
    summaryQuery.isLoading ||
    providersQuery.isLoading ||
    stagesQuery.isLoading ||
    renewalsQuery.isLoading ||
    modelsQuery.isLoading ||
    balanceQuery.isLoading ||
    overviewQuery.isLoading;

  const isError =
    summaryQuery.isError || providersQuery.isError || stagesQuery.isError;

  const handleRefresh = () => {
    void overviewQuery.refetch();
    void summaryQuery.refetch();
    void providersQuery.refetch();
    void stagesQuery.refetch();
    void renewalsQuery.refetch();
    void cbQuery.refetch();
    void modelsQuery.refetch();
    void balanceQuery.refetch();
  };

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-6 p-4 lg:p-6">
      {/* Header bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="rounded-md bg-accent-primary/10 p-1.5 text-accent-primary">
              <Gauge className="h-5 w-5" aria-hidden="true" />
            </div>
            <h1 className="text-xl font-semibold tracking-tight text-text-primary">
              EvalLaps — Observabilité LLMOps &amp; FinOps
            </h1>
          </div>
          <p className="text-xs text-text-secondary">
            Dashboard visuel des quotas, vélocité des tokens et répartition de charge en temps réel.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Time window selector */}
          <div
            role="group"
            aria-label="Période temporelle"
            className="inline-flex rounded-md border border-border-subtle bg-surface p-0.5"
          >
            {WINDOW_OPTIONS.map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={days === option}
                onClick={() => setDays(option)}
                className={`min-h-7 rounded px-3 font-mono text-xs transition-colors ${
                  days === option
                    ? "bg-card text-text-primary shadow-xs"
                    : "text-text-secondary hover:text-text-primary"
                }`}
              >
                {option}j
              </button>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isLoading}
            className="gap-1.5 font-mono text-xs"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`}
              aria-hidden="true"
            />
            Actualiser
          </Button>
        </div>
      </div>

      {/* Error state */}
      {isError && (
        <div
          role="alert"
          className="flex items-start gap-2.5 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-xs text-red-300"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" aria-hidden="true" />
          <div className="space-y-1">
            <p className="font-semibold">Impossible de charger la télémétrie EvalLaps.</p>
            <p className="text-red-300/80">
              Vérifiez la connexion à PostgreSQL schema <code>app_meta</code> ou réessayez.
            </p>
          </div>
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Skeleton className="h-28 rounded-lg" />
            <Skeleton className="h-28 rounded-lg" />
            <Skeleton className="h-28 rounded-lg" />
            <Skeleton className="h-28 rounded-lg" />
          </div>
          <Skeleton className="h-72 rounded-lg" />
          <Skeleton className="h-80 rounded-lg" />
        </div>
      )}

      {/* Content */}
      {!isLoading && !isError && (
        <div className="space-y-6">
          {/* 1. Google AI Studio Style Executive Quota & Resets Hero */}
          {overviewQuery.data && <QuotaHero overview={overviewQuery.data} />}

          {/* 2. Visual Analytics Row: Time-series Burn Rate (Left) + Model Distribution Donut (Right) */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <TokenBurnChart />
            <ModelDistributionChart models={modelsQuery.data?.models ?? []} />
          </div>

          {/* 3. Traffic & Quotas Row: Input vs Output Bar (Left) + Load Balancer Visual Gauges (Right) */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <TokenIoChart models={modelsQuery.data?.models ?? []} />
            {balanceQuery.data && <LoadBalancerVisual distribution={balanceQuery.data} />}
          </div>

          {/* 4. Provider Visual Cards Grid */}
          <ProviderCards
            providers={providersQuery.data ?? []}
            catalog={renewalsQuery.data ?? []}
          />

          {/* 5. Agent Stage Pipeline Funnel Chart */}
          <StageChart stages={stagesQuery.data ?? []} />
        </div>
      )}
    </div>
  );
}
