export interface HealthResponse {
  status: "ok" | "degraded";
  service: string;
  version: string;
  environment: string;
  database_status: "connected" | "unavailable";
  llm_provider: string;
  llm_configured: boolean;
  llm_providers_armed?: string[];
  llm_tokens_armed?: number;
  llm_fallback_active?: boolean;
  llm_quarantined_providers?: string[];
}

export interface ConnectionSummary {
  id: string;
  display_name: string;
  description: string;
  dialect: "postgresql";
  read_only: boolean;
  target_schemas: string[];
  statement_timeout_ms: number;
  max_rows: number;
  is_default: boolean;
}

export interface ConnectionListResponse {
  default_connection_id: string;
  connections: ConnectionSummary[];
}

export interface ColumnMetadata {
  name: string;
  data_type: string;
  udt_name: string;
  is_nullable: boolean;
  default_value: string | null;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  foreign_key_target: string | null;
}

export interface ForeignKeyMetadata {
  constraint_name: string;
  column_name: string;
  referenced_schema: string;
  referenced_table: string;
  referenced_column: string;
}

export interface IndexMetadata {
  name: string;
  columns: string[];
  is_unique: boolean;
  is_primary: boolean;
  index_type: string;
}

export interface TableMetadata {
  schema_name: string;
  table_name: string;
  estimated_row_count: number;
  total_size_bytes: number;
  columns: ColumnMetadata[];
  primary_key_columns: string[];
  foreign_keys: ForeignKeyMetadata[];
  indexes: IndexMetadata[];
}

export interface SchemaIntrospectionResponse {
  connection_id: string;
  dialect: "postgresql";
  read_only: boolean;
  schemas: string[];
  table_count: number;
  tables: TableMetadata[];
}

export interface SecurityCheckResponse {
  rule: string;
  passed: boolean;
  detail: string;
}

export interface ValidateSQLResponse {
  connection_id: string;
  security_status: "passed" | "blocked";
  original_sql: string;
  validated_sql: string | null;
  enforced_limit: number | null;
  limit_was_injected: boolean;
  limit_was_clamped: boolean;
  violations: string[];
  checks: SecurityCheckResponse[];
}

export interface PlanFindingResponse {
  severity: "info" | "warning" | "high" | string;
  category: string;
  title: string;
  detail: string;
  suggestion: string;
}

export interface PlanSummaryResponse {
  root_node_type: string;
  startup_cost: number;
  total_cost: number;
  estimated_rows: number;
  plan_width: number;
  node_types: string[];
  has_sort: boolean;
  has_nested_loop: boolean;
  has_hash_join: boolean;
  findings: PlanFindingResponse[];
}

export type ExecutionStatus = "success" | "error" | "timeout" | "skipped" | "cancelled";

export interface ExecuteSQLResponse {
  run_id: string | null;
  connection_id: string;
  original_sql: string;
  validated_sql: string | null;
  security_status: "passed" | "blocked";
  security_violations: string[];
  security_checks: SecurityCheckResponse[];
  enforced_limit: number | null;
  limit_was_injected: boolean;
  limit_was_clamped: boolean;
  execution_status: ExecutionStatus;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  was_truncated: boolean;
  execution_time_ms: number | null;
  execution_error: string | null;
  explain_plan: Record<string, unknown>[] | null;
  plan_summary: PlanSummaryResponse | null;
  warnings: string[];
}

export type PrimaryStageId =
  | "schema_analyst"
  | "sql_generator"
  | "query_reviewer"
  | "security_gate"
  | "sql_executor"
  | "result_explainer";

export interface StageStatusResponse {
  stage: PrimaryStageId | string;
  status: "completed" | "retrying" | "blocked" | "error" | "skipped";
  attempt: number;
  duration_ms: number;
  summary: string;
}

export interface ExplanationResponse {
  summary: string;
  key_findings: string[];
  caveats: string[];
  suggested_chart: "none" | "bar" | "line" | "area" | "donut" | "horizontal_bar";
}

export interface QueryClassificationResponse {
  intent:
    | "aggregation"
    | "filtering"
    | "trend"
    | "cohort"
    | "anomaly"
    | "comparison"
    | "lookup"
    | "general";
  complexity: "simple" | "moderate" | "complex";
  recommended_strategy: string;
}

export interface OptimizationRecommendationResponse {
  severity: "info" | "warning" | "high";
  category: string;
  title: string;
  detail: string;
  suggestion: string;
  suggested_sql_or_index: string | null;
}

export interface AskQueryResponse {
  run_id: string | null;
  connection_id: string;
  question: string;
  classification?: QueryClassificationResponse | null;
  selected_tables: string[];
  ambiguities: string[];
  candidate_sql: string | null;
  validated_sql: string | null;
  generation_rationale: string | null;
  assumptions: string[];
  review_status: "approved" | "needs_revision" | null;
  review_notes: string[];
  security_status: "passed" | "blocked";
  security_violations: string[];
  security_checks: SecurityCheckResponse[];
  enforced_limit: number | null;
  limit_was_injected: boolean;
  limit_was_clamped: boolean;
  execution_status: ExecutionStatus;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  was_truncated: boolean;
  execution_time_ms: number | null;
  execution_error: string | null;
  explanation: ExplanationResponse | null;
  explain_plan: Record<string, unknown>[] | null;
  plan_summary: PlanSummaryResponse | null;
  optimization_status: "completed" | "partial" | "skipped";
  optimizations: OptimizationRecommendationResponse[];
  warnings: string[];
  stages: StageStatusResponse[];
  total_tokens?: number;
  estimated_savings_usd?: number;
}

export interface SseStageStartedEvent {
  stage: PrimaryStageId;
  label: string;
  attempt: number;
  timestamp: string;
}

export interface SseStageCompletedEvent {
  stage: PrimaryStageId;
  label: string;
  status: "completed" | "retrying" | "blocked" | "error";
  attempt: number;
  duration_ms: number;
  summary: string;
}

export interface SseStageRetryEvent {
  stage: PrimaryStageId;
  attempt: number;
  reason: string;
}

export interface SseSecurityBlockedEvent {
  stage: "security_gate";
  label: string;
  violations: string[];
  sql: string;
}

export interface SseOptimizationStartedEvent {
  stage: "optimization_agent";
  timestamp: string;
}

export interface SseOptimizationCompletedEvent {
  stage: "optimization_agent";
  status: "completed" | "partial" | "skipped";
  duration_ms: number;
  recommendation_count: number;
  recommendations: OptimizationRecommendationResponse[];
}

export interface SseErrorEvent {
  code: string;
  message: string;
}

export interface QueryRunHistoryItem {
  id: string;
  connection_id: string;
  actor_id: string;
  mode: "nl" | "manual_sql";
  natural_language_prompt: string | null;
  generated_sql: string | null;
  validated_sql: string | null;
  security_status: "passed" | "blocked";
  review_status: string | null;
  execution_status: ExecutionStatus;
  execution_time_ms: number | null;
  row_count: number | null;
  was_truncated: boolean;
  optimization_count: number;
  created_at: string;
}

export interface QueryRunHistoryDetail extends QueryRunHistoryItem {
  security_violations: string[];
  explain_plan: Record<string, unknown>[] | Record<string, unknown> | null;
  explanation_text: string | null;
  optimizations: OptimizationRecommendationResponse[];
}

export interface QueryRunHistoryResponse {
  total: number;
  limit: number;
  offset: number;
  items: QueryRunHistoryItem[];
}

export interface AnalyticsSummary {
  total_runs: number;
  passed_runs: number;
  blocked_runs: number;
  failed_runs: number;
  cancelled_runs: number;
  optimized_runs: number;
  avg_execution_time_ms: number | null;
  p95_execution_time_ms: number | null;
}

export interface ExecutionTrendPoint {
  date: string;
  avg_execution_time_ms: number;
  max_execution_time_ms: number;
  run_count: number;
}

export interface QueryComparisonItem {
  run_id: string;
  label: string;
  mode: "nl" | "manual_sql";
  execution_time_ms: number;
  row_count: number;
}

export interface StatusDistributionItem {
  status: "passed" | "blocked" | "failed" | "optimized";
  count: number;
}

export interface ActivityBucket {
  date: string;
  total: number;
  nl_count: number;
  manual_sql_count: number;
}

export interface DatabaseTableStat {
  table_name: string;
  schema_name: string;
  estimated_row_count: number;
  total_size_bytes: number;
  index_count: number;
}

export interface AnalyticsDashboardResponse {
  connection_id: string;
  window_days: number;
  summary: AnalyticsSummary;
  execution_trends: ExecutionTrendPoint[];
  query_comparisons: QueryComparisonItem[];
  status_distribution: StatusDistributionItem[];
  activity_over_time: ActivityBucket[];
  database_statistics: DatabaseTableStat[];
}

export interface GoldenTestCase {
  id: string;
  question: string;
  category: string;
  difficulty: "easy" | "medium" | "hard";
  golden_sql: string;
  description: string;
}

export interface EvalCaseResult {
  case_id: string;
  question: string;
  difficulty: "easy" | "medium" | "hard";
  category: string;
  status: "passed" | "mismatch" | "error" | "blocked";
  vast_passed: boolean;
  execution_accuracy: boolean;
  golden_sql: string;
  generated_sql: string | null;
  golden_row_count: number;
  candidate_row_count: number | null;
  latency_ms: number;
  error_message: string | null;
  details?: Record<string, unknown>;
}

export interface DifficultyMetric {
  total: number;
  passed: number;
  accuracy_percentage: number;
}

export interface CategoryMetric {
  total: number;
  passed: number;
  accuracy_percentage: number;
}

export interface EvalRunSummary {
  run_id: string;
  model_name: string;
  timestamp: string;
  total_cases: number;
  passed_cases: number;
  vast_passed_count: number;
  accuracy_percentage: number;
  vast_percentage: number;
  avg_latency_ms: number;
  by_difficulty: Record<string, DifficultyMetric>;
  by_category: Record<string, CategoryMetric>;
}

export interface EvalRunResponse {
  summary: EvalRunSummary;
  results: EvalCaseResult[];
}

export interface EvalRunRequest {
  case_ids?: string[];
  difficulty?: "easy" | "medium" | "hard";
  mock_run?: boolean;
}
