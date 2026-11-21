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
      <div className="my-3 flex items-center justify-between rounded-lg border border-sky-500/30 bg-sky-500/10 p-3">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-sky-400 animate-pulse" aria-hidden="true" />
          <span className="font-mono text-xs text-slate-300">Prochaine Inférence :</span>
          <span className="font-mono text-xs font-bold text-sky-300">
            {distribution.next_dispatched_model}
          </span>
        </div>
        <Badge variant="cyan" className="font-mono text-[10px] border-sky-400/40 text-sky-300">
          {distribution.next_dispatched_provider.toUpperCase()}
        </Badge>
      </div>

      {/* Traffic Share Visual Bars */}
      <div className="space-y-3 my-1">
        {distribution.shares.slice(0, 5).map((share) => (
          <div key={`${share.provider_name}-${share.key_fingerprint}`} className="space-y-1">
            <div className="flex items-center justify-between font-mono text-[11px] tabular-nums">
              <div className="flex items-center gap-2">
                <span
                  className={`h-2 w-2 rounded-full ${
                    share.is_healthy ? "bg-emerald-400" : "bg-amber-400"
                  }`}
                />
                <span className="font-medium text-slate-200 capitalize">{share.provider_name}</span>
                <span className="text-slate-400 text-[10px]">{share.key_fingerprint}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-slate-400">{formatNumber(share.today_tokens)} toks</span>
                <span className="font-bold text-sky-400 w-10 text-right">
                  {share.traffic_share_percentage}%
                </span>
              </div>
            </div>

            {/* Visual Gauge Bar */}
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800/90 border border-slate-700/50 p-[0.5px]">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  share.is_healthy
                    ? "bg-gradient-to-r from-sky-400 to-cyan-300"
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
