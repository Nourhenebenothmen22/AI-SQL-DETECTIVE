"use client";

import { CheckCircle2, Clock, RefreshCw, ShieldCheck, Zap } from "lucide-react";

import { formatCurrencyUsd, formatDurationMs, formatNumber } from "@/lib/format";
import type { ProviderRenewalMeta, ProviderUsageSummary } from "@/types/evallaps";

function RenewalBadge({ meta }: { meta: ProviderRenewalMeta }) {
  if (meta.renewal_type === "sliding_window_1m") {
    return (
      <span className="inline-flex items-center gap-1 rounded bg-blue-500/15 px-2 py-0.5 font-mono text-[11px] font-medium text-blue-400">
        <RefreshCw className="h-3 w-3 animate-spin-slow" aria-hidden="true" />
        Glissant 60s (Auto)
      </span>
    );
  }
  if (meta.renewal_type === "rolling_daily_24h") {
    return (
      <span className="inline-flex items-center gap-1 rounded bg-emerald-500/15 px-2 py-0.5 font-mono text-[11px] font-medium text-emerald-400">
        <Clock className="h-3 w-3" aria-hidden="true" />
        Quotidien 24h (00:00 UTC)
      </span>
    );
  }
  if (meta.renewal_type === "monthly_credits") {
    return (
      <span className="inline-flex items-center gap-1 rounded bg-purple-500/15 px-2 py-0.5 font-mono text-[11px] font-medium text-purple-400">
        <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
        Mensuel (1er du mois)
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded bg-amber-500/15 px-2 py-0.5 font-mono text-[11px] font-medium text-amber-400">
      <Zap className="h-3 w-3" aria-hidden="true" />
      Solde Statique / Crédits
    </span>
  );
}

export function ProviderTable({
  providers,
  catalog,
}: {
  providers: ProviderUsageSummary[];
  catalog: ProviderRenewalMeta[];
}) {
  return (
    <div className="space-y-6">
      {/* 1. Fournisseurs Actifs (Consommation & Télémétrie) */}
      <div className="rounded-lg border border-border-subtle bg-card shadow-sm">
        <div className="border-b border-border-subtle p-4">
          <h2 className="text-sm font-semibold tracking-tight text-text-primary">
            Consommation &amp; Santé par Fournisseur LLM
          </h2>
          <p className="text-xs text-text-secondary">
            Statut temps réel, taux de requêtes HTTP 200 vs 429, latence moyenne et économies générées.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-sans text-xs">
            <thead className="border-b border-border-subtle bg-surface/50 font-mono text-[11px] uppercase tracking-wider text-text-secondary">
              <tr>
                <th scope="col" className="px-4 py-3">Fournisseur</th>
                <th scope="col" className="px-4 py-3">Renouvellement Quota</th>
                <th scope="col" className="px-4 py-3">Plafond Free Tier</th>
                <th scope="col" className="px-4 py-3 text-right">Tokens Consommés</th>
                <th scope="col" className="px-4 py-3 text-right">Économies (USD)</th>
                <th scope="col" className="px-4 py-3 text-center">Succès / Erreurs</th>
                <th scope="col" className="px-4 py-3 text-right">Latence Moy.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {providers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-text-secondary">
                    Aucun fournisseur n&apos;a encore enregistré d&apos;activité sur cette période.
                  </td>
                </tr>
              ) : (
                providers.map((p) => (
                  <tr key={p.provider_name} className="hover:bg-surface/30">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-text-primary">{p.renewal.display_name}</span>
                        <code className="rounded bg-surface px-1.5 py-0.5 font-mono text-[10px] text-text-secondary">
                          {p.provider_name}
                        </code>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <RenewalBadge meta={p.renewal} />
                    </td>
                    <td className="px-4 py-3 font-mono text-[11px] text-text-secondary">
                      {p.renewal.free_tier_limits_label}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-text-primary font-medium">
                      {formatNumber(p.total_tokens)}
                      <span className="block text-[10px] text-text-secondary">
                        {formatNumber(p.prompt_tokens)} in / {formatNumber(p.completion_tokens)} out
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono font-medium text-emerald-400">
                      {formatCurrencyUsd(p.estimated_savings_usd)}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="inline-flex items-center gap-1 font-mono text-xs text-text-primary">
                        <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" aria-hidden="true" />
                        {p.success_calls} / {p.total_calls}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-text-primary">
                      {formatDurationMs(p.avg_latency_ms)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 2. Diagnostic & Catalogue des 10 Clés API Gratuites */}
      <div className="rounded-lg border border-border-subtle bg-card shadow-sm">
        <div className="border-b border-border-subtle p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold tracking-tight text-text-primary">
                Catalogue &amp; Règles de Renouvellement des Clés API (100% Free Tiers)
              </h2>
              <p className="text-xs text-text-secondary">
                Diagnostique de réinitialisation automatique pour comprendre la pérennité de chaque clé configurée.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 divide-y divide-border-subtle sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-3">
          {catalog.map((cat) => (
            <div key={cat.provider_name} className="p-4 space-y-2 hover:bg-surface/20 transition-colors">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-text-primary text-xs">{cat.display_name}</span>
                <RenewalBadge meta={cat} />
              </div>
              <p className="font-mono text-[11px] text-accent-secondary">
                {cat.free_tier_limits_label}
              </p>
              <p className="text-xs text-text-secondary leading-relaxed">
                {cat.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
