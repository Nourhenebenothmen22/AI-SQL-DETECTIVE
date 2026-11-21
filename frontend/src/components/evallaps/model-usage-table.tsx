"use client";

import { Cpu } from "lucide-react";

import { formatCurrencyUsd, formatNumber } from "@/lib/format";
import type { ModelUsageSummary } from "@/types/evallaps";

interface ModelUsageTableProps {
  models: ModelUsageSummary[];
}

export function ModelUsageTable({ models }: ModelUsageTableProps) {
  if (models.length === 0) {
    return (
      <div className="rounded-lg border border-border-subtle bg-card p-6 text-center shadow-sm">
        <Cpu className="mx-auto h-8 w-8 text-text-secondary opacity-40" aria-hidden="true" />
        <p className="mt-2 text-sm font-medium text-text-primary">Aucune métrique de modèle enregistrée</p>
        <p className="mt-1 text-xs text-text-secondary">
          Les appels cognitifs aux agents enregistreront automatiquement la consommation par modèle.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border-subtle bg-card shadow-sm">
      <div className="border-b border-border-subtle px-4 py-3">
        <h3 className="text-sm font-semibold text-text-primary">
          Consommation Détaillée par Modèle &amp; Jauges de Quotas
        </h3>
        <p className="text-xs text-text-secondary">
          Décomposition des coûts d&apos;entrée (Prompt) vs sortie (Génération) et estimation du solde restant.
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="border-b border-border-subtle bg-surface/50 font-mono text-[11px] uppercase tracking-wider text-text-secondary">
            <tr>
              <th scope="col" className="px-4 py-3">Modèle &amp; Fournisseur</th>
              <th scope="col" className="px-4 py-3 text-right">Prompt Tokens (Input $)</th>
              <th scope="col" className="px-4 py-3 text-right">Completion Tokens (Output $)</th>
              <th scope="col" className="px-4 py-3 text-right">Total Tokens</th>
              <th scope="col" className="px-4 py-3 text-right">Économies FinOps</th>
              <th scope="col" className="px-4 py-3">Quota Restant Estimé</th>
              <th scope="col" className="px-4 py-3 text-center">Appels (Succès / Err)</th>
              <th scope="col" className="px-4 py-3 text-right">Latence Moy.</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-subtle font-mono">
            {models.map((model) => {
              const isQuotaLow = model.usage_percentage > 80;
              return (
                <tr key={`${model.provider_name}-${model.model_name}`} className="transition-colors hover:bg-surface/30">
                  {/* Modèle & Fournisseur */}
                  <td className="px-4 py-3">
                    <p className="font-semibold text-text-primary font-mono text-xs">{model.model_name}</p>
                    <div className="mt-0.5 flex items-center gap-1.5 font-sans text-[11px] text-text-secondary">
                      <span className="inline-block h-1.5 w-1.5 rounded-full bg-cyan-400" />
                      {model.display_name}
                    </div>
                  </td>

                  {/* Input Tokens & Cost */}
                  <td className="px-4 py-3 text-right">
                    <span className="text-text-primary">{formatNumber(model.prompt_tokens)}</span>
                    <p className="text-[10px] text-cyan-400">{formatCurrencyUsd(model.input_cost_usd)}</p>
                  </td>

                  {/* Output Tokens & Cost */}
                  <td className="px-4 py-3 text-right">
                    <span className="text-text-primary">{formatNumber(model.completion_tokens)}</span>
                    <p className="text-[10px] text-emerald-400">{formatCurrencyUsd(model.output_cost_usd)}</p>
                  </td>

                  {/* Total Tokens */}
                  <td className="px-4 py-3 text-right font-semibold text-text-primary">
                    {formatNumber(model.total_tokens)}
                  </td>

                  {/* Économies FinOps */}
                  <td className="px-4 py-3 text-right font-semibold text-emerald-400">
                    {formatCurrencyUsd(model.total_savings_usd)}
                  </td>

                  {/* Quota Restant Estimé */}
                  <td className="px-4 py-3 min-w-[180px]">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className={isQuotaLow ? "text-amber-400 font-semibold" : "text-emerald-400 font-semibold"}>
                        {formatNumber(model.estimated_remaining_tokens)} restants
                      </span>
                      <span className="text-[10px] text-text-secondary">
                        {model.usage_percentage}%
                      </span>
                    </div>
                    <div className="mt-1 h-1.5 w-full rounded-full bg-border-subtle overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${
                          isQuotaLow ? "bg-amber-400" : "bg-emerald-400"
                        }`}
                        style={{ width: `${Math.min(100, Math.max(2, model.usage_percentage))}%` }}
                      />
                    </div>
                    <p className="mt-0.5 text-[10px] text-text-secondary">
                      sur {formatNumber(model.estimated_daily_quota_tokens)} / jour
                    </p>
                  </td>

                  {/* Appels */}
                  <td className="px-4 py-3 text-center">
                    <span className="text-text-primary font-medium">{model.total_calls}</span>{" "}
                    <span className="text-emerald-400">({model.success_calls}</span> /{" "}
                    <span className={model.error_calls > 0 ? "text-rose-400" : "text-text-secondary"}>
                      {model.error_calls})
                    </span>
                  </td>

                  {/* Latence Moyenne */}
                  <td className="px-4 py-3 text-right text-text-secondary">
                    {model.avg_latency_ms > 0 ? `${model.avg_latency_ms} ms` : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
