"use client";

import { ArrowRight, Award, BarChart3, Coins, Layers, Scale, ShieldCheck } from "lucide-react";

import { formatCurrencyUsd, formatNumber } from "@/lib/format";
import type { LoadBalancerDistribution, ModelBreakdownResponse } from "@/types/evallaps";

interface LoadBalancerHudProps {
  distribution: LoadBalancerDistribution;
  breakdown: ModelBreakdownResponse;
}

export function LoadBalancerHud({ distribution, breakdown }: LoadBalancerHudProps) {
  const extremes = breakdown.extremes;
  const mostUsed = extremes.most_used_model;
  const leastUsed = extremes.least_used_model;

  return (
    <div className="space-y-4">
      {/* 1. Header & Strategy banner */}
      <div className="rounded-lg border border-accent-primary/30 bg-card p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3">
          <div className="flex items-center gap-2">
            <div className="rounded-md bg-accent-primary/15 p-1.5 text-accent-primary">
              <Layers className="h-4 w-4" aria-hidden="true" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-text-primary">
                Load Balancer Quota-Aware (Répartition Déterministe Zéro If-Else)
              </h2>
              <p className="text-xs text-text-secondary">
                Équilibrage actif par moindre charge : la requête est automatiquement attribuée au modèle sain ayant consommé le moins de tokens.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-400">
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
              {distribution.total_healthy_providers} clés saines actives
            </span>
          </div>
        </div>

        {/* 2. Top Grid: Next Dispatched + Input Cost + Output Cost */}
        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {/* Next Candidate */}
          <div className="rounded-md border border-border-subtle bg-surface/50 p-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] uppercase tracking-wider text-text-secondary">
                Prochain Modèle Désigné
              </span>
              <ArrowRight className="h-3.5 w-3.5 text-accent-primary" aria-hidden="true" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <p className="font-mono text-sm font-semibold text-accent-primary truncate">
                {distribution.next_dispatched_model}
              </p>
            </div>
            <p className="mt-1 font-mono text-[11px] text-text-secondary">
              Fournisseur : <strong className="text-text-primary uppercase">{distribution.next_dispatched_provider}</strong> · Clé : <span className="text-cyan-400">{distribution.dispatched_key_fingerprint}</span>
            </p>
          </div>

          {/* Input Cost (Prompt) */}
          <div className="rounded-md border border-border-subtle bg-surface/50 p-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] uppercase tracking-wider text-text-secondary">
                Coût Estimé Input (Prompt)
              </span>
              <Coins className="h-3.5 w-3.5 text-cyan-400" aria-hidden="true" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <p className="text-lg font-semibold text-cyan-400">
                {formatCurrencyUsd(breakdown.total_input_cost_usd)}
              </p>
              <span className="rounded bg-cyan-500/15 px-1.5 py-0.5 font-mono text-[10px] text-cyan-300">
                $2.50 / 1M tokens
              </span>
            </div>
            <p className="mt-1 text-[11px] text-text-secondary">
              Économisé grâce au pool gratuit
            </p>
          </div>

          {/* Output Cost (Completion) */}
          <div className="rounded-md border border-border-subtle bg-surface/50 p-3">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] uppercase tracking-wider text-text-secondary">
                Coût Estimé Output (Génération)
              </span>
              <Coins className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
            </div>
            <div className="mt-2 flex items-baseline gap-2">
              <p className="text-lg font-semibold text-emerald-400">
                {formatCurrencyUsd(breakdown.total_output_cost_usd)}
              </p>
              <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 font-mono text-[10px] text-emerald-300">
                $10.00 / 1M tokens
              </span>
            </div>
            <p className="mt-1 text-[11px] text-text-secondary">
              Économisé grâce au pool gratuit
            </p>
          </div>
        </div>

        {/* 3. Extremes: Top Sollicité vs Moins Sollicité */}
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {/* Most Used Model */}
          <div className="rounded-md border border-amber-500/20 bg-amber-500/5 p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Award className="h-4 w-4 text-amber-400" aria-hidden="true" />
                <span className="font-mono text-xs font-semibold text-amber-300 uppercase tracking-wider">
                  Modèle le Plus Utilisé (Top Load)
                </span>
              </div>
              <span className="font-mono text-xs text-amber-400">
                {mostUsed ? `${formatNumber(mostUsed.total_tokens)} tokens` : "Aucun appel"}
              </span>
            </div>
            {mostUsed ? (
              <div className="mt-2">
                <p className="font-mono text-sm font-semibold text-text-primary">
                  {mostUsed.model_name}
                </p>
                <div className="mt-1 flex items-center gap-3 text-xs text-text-secondary">
                  <span>Fournisseur : <strong className="text-text-primary">{mostUsed.display_name}</strong></span>
                  <span>·</span>
                  <span>Requêtes : <strong className="text-text-primary">{mostUsed.total_calls}</strong></span>
                  <span>·</span>
                  <span>Économies : <strong className="text-emerald-400">{formatCurrencyUsd(mostUsed.total_savings_usd)}</strong></span>
                </div>
              </div>
            ) : (
              <p className="mt-2 text-xs text-text-secondary">En attente de requêtes dans la période sélectionnée.</p>
            )}
          </div>

          {/* Least Used Model */}
          <div className="rounded-md border border-indigo-500/20 bg-indigo-500/5 p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Scale className="h-4 w-4 text-indigo-400" aria-hidden="true" />
                <span className="font-mono text-xs font-semibold text-indigo-300 uppercase tracking-wider">
                  Modèle le Moins Utilisé (Réserve Quota)
                </span>
              </div>
              <span className="font-mono text-xs text-indigo-400">
                {leastUsed ? `${formatNumber(leastUsed.total_tokens)} tokens` : "Aucun appel"}
              </span>
            </div>
            {leastUsed ? (
              <div className="mt-2">
                <p className="font-mono text-sm font-semibold text-text-primary">
                  {leastUsed.model_name}
                </p>
                <div className="mt-1 flex items-center gap-3 text-xs text-text-secondary">
                  <span>Fournisseur : <strong className="text-text-primary">{leastUsed.display_name}</strong></span>
                  <span>·</span>
                  <span>Quota Restant : <strong className="text-emerald-400">{formatNumber(leastUsed.estimated_remaining_tokens)} tokens</strong></span>
                  <span>·</span>
                  <span>Requêtes : <strong className="text-text-primary">{leastUsed.total_calls}</strong></span>
                </div>
              </div>
            ) : (
              <p className="mt-2 text-xs text-text-secondary">En attente de requêtes dans la période sélectionnée.</p>
            )}
          </div>
        </div>

        {/* 4. Live Shares Gauge */}
        {distribution.shares.length > 0 && (
          <div className="mt-4 border-t border-border-subtle pt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs text-text-secondary flex items-center gap-1.5">
                <BarChart3 className="h-3.5 w-3.5 text-text-secondary" aria-hidden="true" />
                Répartition des Charges du Jour (Traffic Share par Clé)
              </span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
              {distribution.shares.map((share) => (
                <div
                  key={`${share.provider_name}-${share.key_fingerprint}`}
                  className="rounded border border-border-subtle bg-surface/40 p-2 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-text-primary uppercase text-[11px]">
                      {share.display_name}
                    </span>
                    <span className={`font-mono text-[10px] rounded px-1.5 py-0.2 ${
                      share.is_healthy ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                    }`}>
                      {share.key_fingerprint}
                    </span>
                  </div>
                  <div className="mt-1.5 flex items-center justify-between text-[11px] text-text-secondary">
                    <span>{formatNumber(share.today_tokens)} tokens</span>
                    <span className="font-mono text-accent-primary font-semibold">
                      {share.traffic_share_percentage}%
                    </span>
                  </div>
                  <div className="mt-1 h-1.5 w-full rounded-full bg-border-subtle overflow-hidden">
                    <div
                      className="h-full bg-accent-primary transition-all duration-300"
                      style={{ width: `${Math.min(100, Math.max(3, share.traffic_share_percentage))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
