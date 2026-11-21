export type RenewalType =
  | "sliding_window_1m"
  | "rolling_daily_24h"
  | "monthly_credits"
  | "quota_static_tier";

export interface ProviderRenewalMeta {
  provider_name: string;
  display_name: string;
  renewal_type: RenewalType | string;
  renewal_window_label: string;
  free_tier_limits_label: string;
  is_auto_renewable: boolean;
  description: string;
}

export interface ProviderUsageSummary {
  provider_name: string;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_savings_usd: number;
  real_cost_usd: number;
  total_calls: number;
  success_calls: number;
  error_calls: number;
  avg_latency_ms: number;
  renewal: ProviderRenewalMeta;
}

export interface StageUsageSummary {
  stage_id: string;
  stage_label: string;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  estimated_savings_usd: number;
  total_calls: number;
  avg_latency_ms: number;
}

export interface EvalLapsSummary {
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_savings_usd: number;
  total_real_cost_usd: number;
  total_calls: number;
  today_tokens: number;
  today_savings_usd: number;
  this_month_tokens: number;
  this_month_savings_usd: number;
  providers_count: number;
  top_provider: string | null;
}

export interface TokenLedgerItem {
  id: string;
  run_id: string | null;
  stage_id: string;
  provider_name: string;
  model_name: string;
  key_fingerprint: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_savings_usd: number;
  real_cost_usd: number;
  http_status: number;
  latency_ms: number;
  recorded_at: string;
}
