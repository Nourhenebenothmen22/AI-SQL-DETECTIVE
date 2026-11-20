"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  Boxes,
  CheckCircle2,
  Database,
  FlaskConical,
  Loader2,
  RotateCcw,
  ShoppingBag,
  Sparkles,
  Star,
  TrendingUp,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api-client";
import type { ScenarioGenerateResponse, ScenarioResetResponse } from "@/types/api";

const PRESET_SCENARIOS = [
  {
    title: "Black Friday Flash Sale",
    prompt:
      "Simulate a massive Black Friday flash sale with 120 delivered orders in the Electronics category, high order totals, and 5 critical inventory stockouts.",
  },
  {
    title: "VIP Customer Churn Spike",
    prompt:
      "Simulate a customer churn wave where 25 VIP orders are abruptly cancelled, accompanied by 8 low-rating customer reviews expressing delivery delays.",
  },
  {
    title: "Wholesale Restock & Inventory Surge",
    prompt:
      "Simulate a major wholesale expansion with 40 high-volume wholesale orders and positive inventory restock across all three regional warehouses.",
  },
] as const;

export default function SandboxPage() {
  const queryClient = useQueryClient();
  const [prompt, setPrompt] = useState<string>(PRESET_SCENARIOS[0].prompt);
  const [lastResult, setLastResult] = useState<ScenarioGenerateResponse | null>(null);
  const [resetMessage, setResetMessage] = useState<string | null>(null);

  const generateMutation = useMutation({
    mutationFn: (scenarioPrompt: string) =>
      apiClient.generateScenario({ scenario_prompt: scenarioPrompt }),
    onSuccess: (data) => {
      setLastResult(data);
      setResetMessage(null);
      void queryClient.invalidateQueries({ queryKey: ["schema"] });
      void queryClient.invalidateQueries({ queryKey: ["analytics"] });
      void queryClient.invalidateQueries({ queryKey: ["history"] });
    },
  });

  const resetMutation = useMutation({
    mutationFn: () => apiClient.resetDatabaseScenario(),
    onSuccess: (data: ScenarioResetResponse) => {
      setResetMessage(data.message);
      setLastResult(null);
      void queryClient.invalidateQueries({ queryKey: ["schema"] });
      void queryClient.invalidateQueries({ queryKey: ["analytics"] });
      void queryClient.invalidateQueries({ queryKey: ["history"] });
    },
  });

  const handleSimulate = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim().length < 5 || generateMutation.isPending) return;
    generateMutation.mutate(prompt.trim());
  };

  const handleReset = () => {
    if (resetMutation.isPending) return;
    resetMutation.mutate();
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold tracking-tight text-text-primary">
              AI What-If Scenario Sandbox
            </h1>
            <Badge variant="cyan">SANDBOX ACTIVE</Badge>
          </div>
          <p className="mt-1 text-xs text-text-secondary">
            Simulate realistic market events in PostgreSQL 16 using AI to stress-test Workbench
            queries, security bounds, and performance optimizations.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
            disabled={resetMutation.isPending || generateMutation.isPending}
            className="border-status-warning/40 text-status-warning hover:bg-status-warning/10"
          >
            {resetMutation.isPending ? (
              <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
            ) : (
              <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
            )}
            <span>Reset to Golden Seed</span>
          </Button>
        </div>
      </div>

      {/* Reset notification */}
      {resetMessage ? (
        <div className="flex items-center gap-2.5 rounded-lg border border-status-success/40 bg-status-success/10 p-3.5 text-xs text-text-primary">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-status-success" aria-hidden="true" />
          <span>{resetMessage} Database restored to deterministic baseline (12,000 orders).</span>
        </div>
      ) : null}

      {/* Error notification */}
      {generateMutation.isError ? (
        <div className="flex items-center gap-2.5 rounded-lg border border-status-error/40 bg-status-error/10 p-3.5 text-xs text-text-primary">
          <AlertTriangle className="h-4 w-4 shrink-0 text-status-error" aria-hidden="true" />
          <span>
            {generateMutation.error instanceof Error
              ? generateMutation.error.message
              : "Scenario generation failed. Please try again."}
          </span>
        </div>
      ) : null}

      {/* Scenario Composer */}
      <div className="rounded-lg border border-border-subtle bg-card p-4 sm:p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-primary">
            <Sparkles className="h-3.5 w-3.5 text-accent-primary" aria-hidden="true" />
            <span>Natural Language Scenario Prompt</span>
          </div>
          <span className="font-mono text-[11px] text-text-secondary">100% AI-Driven</span>
        </div>

        {/* Quick Presets */}
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] font-medium text-text-muted">Presets:</span>
          {PRESET_SCENARIOS.map((preset) => (
            <button
              key={preset.title}
              type="button"
              disabled={generateMutation.isPending}
              onClick={() => setPrompt(preset.prompt)}
              className="rounded-full border border-border-subtle bg-surface/80 px-2.5 py-0.5 text-[11px] text-text-secondary transition-all hover:border-accent-primary/50 hover:bg-card-hover hover:text-text-primary disabled:opacity-50"
            >
              {preset.title}
            </button>
          ))}
        </div>

        <form onSubmit={handleSimulate} className="mt-3 space-y-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={generateMutation.isPending}
            rows={3}
            placeholder="Describe any business or market scenario to simulate in PostgreSQL..."
            className="w-full resize-y rounded-md border border-border-subtle bg-surface px-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:border-accent-primary focus:outline-hidden focus:ring-1 focus:ring-accent-primary disabled:opacity-60"
          />

          <div className="flex items-center justify-between">
            <span className="text-[11px] text-text-muted">
              AI translates intent into foreign-key consistent records across orders, inventory, and
              reviews.
            </span>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={prompt.trim().length < 5 || generateMutation.isPending}
            >
              {generateMutation.isPending ? (
                <>
                  <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                  <span>Synthesizing Relational Scenario...</span>
                </>
              ) : (
                <>
                  <FlaskConical className="mr-1.5 h-3.5 w-3.5" />
                  <span>Simulate What-If Scenario</span>
                </>
              )}
            </Button>
          </div>
        </form>
      </div>

      {/* Simulation Result Card */}
      {lastResult ? (
        <div className="space-y-4 rounded-lg border border-accent-primary/40 bg-card p-5 shadow-xs shadow-accent-primary/10">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border-subtle pb-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold text-text-primary">
                  {lastResult.scenario_title}
                </h2>
                <Badge variant="indigo">SIMULATION APPLIED</Badge>
              </div>
              <p className="mt-1 text-xs text-text-secondary">{lastResult.scenario_summary}</p>
            </div>
            <Link
              href={`/?q=${encodeURIComponent(lastResult.suggested_workbench_question)}`}
              className="inline-flex items-center gap-1.5 rounded-md border border-accent-secondary/50 bg-accent-secondary/10 px-3 py-1.5 text-xs font-medium text-accent-secondary transition-all hover:bg-accent-secondary/20"
            >
              <span>Inspect in Workbench</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <div className="rounded-md border border-border-subtle/70 bg-surface/50 p-3">
            <div className="font-mono text-[11px] uppercase tracking-wider text-accent-primary">
              Business Dynamics &amp; Rationale
            </div>
            <p className="mt-1 text-xs leading-relaxed text-text-secondary">
              {lastResult.business_rationale}
            </p>
          </div>

          {/* 4 Impact Metrics Grid */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-md border border-border-subtle bg-surface/70 p-3">
              <div className="flex items-center justify-between text-text-secondary">
                <span className="font-mono text-[11px] uppercase tracking-wider">Orders</span>
                <ShoppingBag className="h-4 w-4 text-accent-primary" />
              </div>
              <p className="mt-2 font-mono text-xl font-semibold tabular-nums text-text-primary">
                +{lastResult.impact.orders_inserted}
              </p>
              <p className="mt-0.5 text-[10px] text-text-muted">Simulated orders added</p>
            </div>

            <div className="rounded-md border border-border-subtle bg-surface/70 p-3">
              <div className="flex items-center justify-between text-text-secondary">
                <span className="font-mono text-[11px] uppercase tracking-wider">Line Items</span>
                <TrendingUp className="h-4 w-4 text-accent-secondary" />
              </div>
              <p className="mt-2 font-mono text-xl font-semibold tabular-nums text-text-primary">
                +{lastResult.impact.order_items_inserted}
              </p>
              <p className="mt-0.5 text-[10px] text-text-muted">Order items linked to products</p>
            </div>

            <div className="rounded-md border border-border-subtle bg-surface/70 p-3">
              <div className="flex items-center justify-between text-text-secondary">
                <span className="font-mono text-[11px] uppercase tracking-wider">Inventory</span>
                <Boxes className="h-4 w-4 text-status-warning" />
              </div>
              <p className="mt-2 font-mono text-xl font-semibold tabular-nums text-text-primary">
                {lastResult.impact.inventory_updated}
              </p>
              <p className="mt-0.5 text-[10px] text-text-muted">Warehouse stock quantities updated</p>
            </div>

            <div className="rounded-md border border-border-subtle bg-surface/70 p-3">
              <div className="flex items-center justify-between text-text-secondary">
                <span className="font-mono text-[11px] uppercase tracking-wider">Reviews</span>
                <Star className="h-4 w-4 text-status-success" />
              </div>
              <p className="mt-2 font-mono text-xl font-semibold tabular-nums text-text-primary">
                +{lastResult.impact.reviews_inserted}
              </p>
              <p className="mt-0.5 text-[10px] text-text-muted">Customer ratings generated</p>
            </div>
          </div>

          {/* Workbench Question Suggestion */}
          <div className="flex items-center justify-between rounded-md border border-accent-secondary/30 bg-accent-secondary/10 p-3">
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4 text-accent-secondary" />
              <div>
                <p className="text-[11px] font-medium uppercase tracking-wider text-accent-secondary">
                  Recommended Detective Query:
                </p>
                <p className="text-xs font-medium text-text-primary">
                  &ldquo;{lastResult.suggested_workbench_question}&rdquo;
                </p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
