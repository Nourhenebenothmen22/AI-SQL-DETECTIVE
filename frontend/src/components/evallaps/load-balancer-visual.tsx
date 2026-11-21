"use client";

import { ArrowRight, Layers, ShieldCheck, Zap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { formatNumber } from "@/lib/format";
import type { LoadBalancerDistribution } from "@/types/evallaps";

interface LoadBalancerVisualProps {
  distribution: LoadBalancerDistribution;
}

export function LoadBalancerVisual({ distribution }: LoadBalancerVisualProps) {
  return (
    <div className="flex h-full flex-col justify-between rounded-xl border border-border-subtle bg-card p-5 shadow-sm">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3">
        <div className="flex items-center gap-2">
          <div className="rounded-md bg-accent-primary/10 p-1.5 text-accent-primary">
            <Layers className="h-4 w-4" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-sm font-semibold tracking-tight text-text-primary">
              Load Balancer Déterministe (Moindre Charge)
            </h3>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 font-mono text-[11px] font-medium text-emerald-400">
            <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
            {distribution.total_healthy_providers} clés actives
          </span>
        </div>
      </div>

      {/* Next candidate highlight pill */}
      <div className="my-3 flex items-center justify-between rounded-lg border border-accent-primary/30 bg-accent-primary/10 p-3">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-accent-primary animate-pulse" aria-hidden="true" />
          <span className="font-mono text-xs text-text-secondary">Prochaine Inférence :</span>
          <span className="font-mono text-xs font-bold text-accent-primary">
            {distribution.next_dispatched_model}
          </span>
        </div>
        <Badge variant="cyan" className="font-mono text-[10px]">
          {distribution.next_dispatched_provider.toUpperCase()}
        </Badge>
      </div>

      {/* Traffic Share Visual Bars */}
      <div className="space-y-2.5 my-1">
        {distribution.shares.slice(0, 5).map((share) => (
          <div key={`${share.provider_name}-${share.key_fingerprint}`} className="space-y-1">
            <div className="flex items-center justify-between font-mono text-[11px] tabular-nums">
              <div className="flex items-center gap-2">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${
                    share.is_healthy ? "bg-emerald-400" : "bg-amber-400"
                  }`}
                />
                <span className="font-medium text-text-primary capitalize">{share.provider_name}</span>
                <span className="text-text-secondary text-[10px]">{share.key_fingerprint}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-text-secondary">{formatNumber(share.today_tokens)} toks</span>
                <span className="font-bold text-accent-secondary w-10 text-right">
                  {share.traffic_share_percentage}%
                </span>
              </div>
            </div>

            {/* Visual Gauge Bar */}
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  share.is_healthy
                    ? "bg-gradient-to-r from-accent-primary to-accent-secondary"
                    : "bg-amber-400"
                }`}
                style={{ width: `${Math.max(2, share.traffic_share_percentage)}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-2 flex items-center justify-between border-t border-border-subtle/50 pt-3 text-[11px] font-mono text-text-secondary">
        <span>Stratégie Algorithmique Pure</span>
        <span className="flex items-center gap-1 text-emerald-400 font-medium">
          <span>0 If-Else</span>
          <ArrowRight className="h-3 w-3" aria-hidden="true" />
        </span>
      </div>
    </div>
  );
}
