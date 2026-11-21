"use client";

import { Coins, Cpu, TrendingUp, Zap } from "lucide-react";

import { formatCurrencyUsd, formatNumber } from "@/lib/format";
import type { EvalLapsSummary } from "@/types/evallaps";

export function SummaryCards({ summary }: { summary: EvalLapsSummary }) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {/* 1. Économies FinOps Cumulées */}
      <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <p className="font-mono text-xs text-text-secondary uppercase tracking-wider">
            Économies FinOps (vs GPT-4o)
          </p>
          <div className="rounded-md bg-emerald-500/10 p-1.5 text-emerald-400">
            <Coins className="h-4 w-4" aria-hidden="true" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <p className="text-2xl font-semibold tracking-tight text-emerald-400">
            {formatCurrencyUsd(summary.total_savings_usd)}
          </p>
          <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 font-mono text-[10px] text-emerald-300">
            Coût Réel : $0.00
          </span>
        </div>
        <p className="mt-1 text-xs text-text-secondary">
          100% Free Tiers · Calculé au barème commercial $2.50 / $10.00 par M
        </p>
      </div>

      {/* 2. Total Tokens Consommés */}
      <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <p className="font-mono text-xs text-text-secondary uppercase tracking-wider">
            Tokens Consommés
          </p>
          <div className="rounded-md bg-accent-primary/10 p-1.5 text-accent-primary">
            <Cpu className="h-4 w-4" aria-hidden="true" />
          </div>
        </div>
        <div className="mt-2">
          <p className="text-2xl font-semibold tracking-tight text-text-primary">
            {formatNumber(summary.total_tokens)}
          </p>
        </div>
        <div className="mt-1 flex items-center gap-3 text-xs text-text-secondary">
          <span>
            Prompt : <strong className="text-text-primary">{formatNumber(summary.prompt_tokens)}</strong>
          </span>
          <span>·</span>
          <span>
            Comp : <strong className="text-text-primary">{formatNumber(summary.completion_tokens)}</strong>
          </span>
        </div>
      </div>

      {/* 3. Consommation Aujourd'hui */}
      <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <p className="font-mono text-xs text-text-secondary uppercase tracking-wider">
            Tokens Aujourd&apos;hui
          </p>
          <div className="rounded-md bg-accent-secondary/10 p-1.5 text-accent-secondary">
            <Zap className="h-4 w-4" aria-hidden="true" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <p className="text-2xl font-semibold tracking-tight text-accent-secondary">
            {formatNumber(summary.today_tokens)}
          </p>
          <span className="font-mono text-xs text-emerald-400">
            +{formatCurrencyUsd(summary.today_savings_usd)}
          </span>
        </div>
        <p className="mt-1 text-xs text-text-secondary">
          Ce mois : {formatNumber(summary.this_month_tokens)} ({formatCurrencyUsd(summary.this_month_savings_usd)})
        </p>
      </div>

      {/* 4. Appels Modèles & Fournisseurs */}
      <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <p className="font-mono text-xs text-text-secondary uppercase tracking-wider">
            Inférences LLM Réussies
          </p>
          <div className="rounded-md bg-indigo-500/10 p-1.5 text-indigo-400">
            <TrendingUp className="h-4 w-4" aria-hidden="true" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <p className="text-2xl font-semibold tracking-tight text-text-primary">
            {formatNumber(summary.total_calls)}
          </p>
          {summary.top_provider && (
            <span className="rounded bg-indigo-500/15 px-1.5 py-0.5 font-mono text-[10px] text-indigo-300">
              Top : {summary.top_provider}
            </span>
          )}
        </div>
        <p className="mt-1 text-xs text-text-secondary">
          {summary.providers_count} fournisseur(s) actif(s) sur le pool gratuit
        </p>
      </div>
    </div>
  );
}
