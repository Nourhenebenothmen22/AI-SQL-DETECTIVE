"use client";

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock,
  ShieldAlert,
  ShieldCheck,
  Zap,
} from "lucide-react";

import type { CircuitBreakerStatusResponse } from "@/types/evallaps";

export function CircuitBreakerHud({
  status,
}: {
  status: CircuitBreakerStatusResponse;
}) {
  return (
    <div className="rounded-lg border border-border-subtle bg-card p-4 shadow-sm space-y-4">
      {/* 1. Header & Global State */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold tracking-tight text-text-primary">
              Circuit Breaker Multi-Tokens &amp; Surveillance des Quotas
            </h2>
            {status.all_healthy ? (
              <span className="inline-flex items-center gap-1 rounded bg-emerald-500/15 px-2 py-0.5 font-mono text-[11px] font-medium text-emerald-400">
                <ShieldCheck className="h-3 w-3" aria-hidden="true" />
                100% Opérationnel
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 rounded bg-amber-500/15 px-2 py-0.5 font-mono text-[11px] font-medium text-amber-400">
                <AlertTriangle className="h-3 w-3" aria-hidden="true" />
                {status.total_quarantined} Quarantaine(s) Active(s)
              </span>
            )}
          </div>
          <p className="text-xs text-text-secondary">
            Détection instantanée des erreurs 429 (Rate Limit) avec rotation immédiate vers les fournisseurs de secours sans interruption de service.
          </p>
        </div>

        {/* Primary provider indicator */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <span className="text-text-secondary">Fournisseur primaire actif :</span>
          <span className="rounded bg-accent-primary/15 px-2 py-1 font-semibold text-accent-primary">
            {status.active_primary_provider.toUpperCase()}
          </span>
        </div>
      </div>

      {/* 2. Quarantined Alert Banner (Shown when any key is quarantined) */}
      {!status.all_healthy && (
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-4 space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-400 shrink-0" aria-hidden="true" />
              <p className="text-xs font-semibold text-amber-300">
                Plafond de quota temporairement atteint sur {status.total_quarantined} clé(s)
              </p>
            </div>
            <span className="rounded bg-emerald-500/20 px-2 py-0.5 font-mono text-[11px] text-emerald-300">
              ✓ Bascule automatique vers {status.active_primary_provider}
            </span>
          </div>

          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
            {status.quarantined.map((q) => (
              <div
                key={q.key_id}
                className="rounded border border-amber-500/20 bg-card/80 p-3 space-y-1.5 font-sans"
              >
                <div className="flex items-center justify-between font-mono text-xs">
                  <span className="font-semibold text-text-primary">{q.display_name}</span>
                  <code className="text-[10px] text-amber-400">{q.key_id}</code>
                </div>
                <p className="text-[11px] text-text-secondary leading-tight truncate" title={q.reason}>
                  Motif : {q.reason}
                </p>
                <div className="flex items-center justify-between pt-1 border-t border-border-subtle font-mono text-[11px]">
                  <span className="text-text-secondary flex items-center gap-1">
                    <Clock className="h-3 w-3 text-amber-400" aria-hidden="true" />
                    Réarmement :
                  </span>
                  <span className="font-semibold text-amber-300">
                    {q.reset_target_label}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Resilient Fallback Chain Pipeline */}
      <div className="space-y-1.5 pt-1">
        <p className="font-mono text-[11px] uppercase tracking-wider text-text-secondary">
          Ordre de cascade de bascule automatique (100% Free-Tier Pool)
        </p>
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          {status.fallback_chain.map((provider, idx) => {
            const isQuarantined = status.quarantined.some((q) => q.provider_name === provider);
            const isPrimary = provider === status.active_primary_provider;

            return (
              <div key={provider} className="flex items-center gap-1.5">
                <span
                  className={`inline-flex items-center gap-1 rounded px-2.5 py-1 text-[11px] transition-colors ${
                    isPrimary
                      ? "border border-accent-primary/50 bg-accent-primary/20 text-accent-primary font-semibold shadow-xs"
                      : isQuarantined
                      ? "border border-amber-500/30 bg-amber-500/10 text-amber-400 line-through opacity-75"
                      : "border border-border-subtle bg-surface text-text-secondary"
                  }`}
                >
                  {isPrimary ? (
                    <Zap className="h-3 w-3 text-accent-primary shrink-0" aria-hidden="true" />
                  ) : isQuarantined ? (
                    <Clock className="h-3 w-3 text-amber-400 shrink-0" aria-hidden="true" />
                  ) : (
                    <CheckCircle2 className="h-3 w-3 text-emerald-400 shrink-0" aria-hidden="true" />
                  )}
                  {provider}
                </span>
                {idx < status.fallback_chain.length - 1 && (
                  <ArrowRight className="h-3 w-3 text-text-secondary/40 shrink-0" aria-hidden="true" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
