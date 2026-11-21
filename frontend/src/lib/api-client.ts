import type {
  AnalyticsDashboardResponse,
  AskQueryResponse,
  ConnectionListResponse,
  EvalRunRequest,
  EvalRunResponse,
  EvalRunSummary,
  ExecuteSQLResponse,
  GoldenTestCase,
  HealthResponse,
  QueryRunHistoryDetail,
  QueryRunHistoryResponse,
  ScenarioGenerateRequest,
  ScenarioGenerateResponse,
  ScenarioResetResponse,
  SchemaIntrospectionResponse,
  SseErrorEvent,
  SseOptimizationCompletedEvent,
  SseOptimizationStartedEvent,
  SseSecurityBlockedEvent,
  SseStageCompletedEvent,
  SseStageRetryEvent,
  SseStageStartedEvent,
  ValidateSQLResponse,
} from "@/types/api";
import type {
  EvalLapsSummary,
  ProviderRenewalMeta,
  ProviderUsageSummary,
  StageUsageSummary,
  TokenLedgerItem,
} from "@/types/evallaps";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ?? "http://localhost:8000";

export class ApiClientError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.detail = detail ?? message;
  }
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string" && body.detail.trim()) {
      return body.detail;
    }
  } catch {
    // Non-JSON error body
  }
  return `API request failed (${response.status})`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const detail = await parseErrorDetail(response);
    throw new ApiClientError(detail, response.status, detail);
  }

  return (await response.json()) as T;
}

export interface StreamAskHandlers {
  onStageStarted?: (event: SseStageStartedEvent) => void;
  onStageCompleted?: (event: SseStageCompletedEvent) => void;
  onStageRetry?: (event: SseStageRetryEvent) => void;
  onSecurityBlocked?: (event: SseSecurityBlockedEvent) => void;
  onOptimizationStarted?: (event: SseOptimizationStartedEvent) => void;
  onOptimizationCompleted?: (event: SseOptimizationCompletedEvent) => void;
  onFinalResult?: (result: AskQueryResponse) => void;
  onError?: (error: SseErrorEvent) => void;
}

function dispatchSseBlock(block: string, handlers: StreamAskHandlers): void {
  let eventName = "";
  const dataLines: string[] = [];

  for (const rawLine of block.split("\n")) {
    const line = rawLine.trimEnd();
    if (!line || line.startsWith(":")) {
      continue;
    }
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (!eventName || dataLines.length === 0) {
    return;
  }

  const payload = JSON.parse(dataLines.join("\n")) as unknown;
  switch (eventName) {
    case "stage_started":
      handlers.onStageStarted?.(payload as SseStageStartedEvent);
      break;
    case "stage_completed":
      handlers.onStageCompleted?.(payload as SseStageCompletedEvent);
      break;
    case "stage_retry":
      handlers.onStageRetry?.(payload as SseStageRetryEvent);
      break;
    case "security_blocked":
      handlers.onSecurityBlocked?.(payload as SseSecurityBlockedEvent);
      break;
    case "optimization_started":
      handlers.onOptimizationStarted?.(payload as SseOptimizationStartedEvent);
      break;
    case "optimization_completed":
      handlers.onOptimizationCompleted?.(payload as SseOptimizationCompletedEvent);
      break;
    case "final_result":
      handlers.onFinalResult?.(payload as AskQueryResponse);
      break;
    case "error":
      handlers.onError?.(payload as SseErrorEvent);
      break;
    default:
      break;
  }
}

export interface HistoryQueryParams {
  connection_id?: string;
  mode?: "nl" | "manual_sql";
  security_status?: "passed" | "blocked";
  execution_status?: "success" | "error" | "timeout" | "skipped" | "cancelled";
  search?: string;
  limit?: number;
  offset?: number;
}

export const apiClient = {
  getHealth(signal?: AbortSignal): Promise<HealthResponse> {
    return requestJson<HealthResponse>("/api/v1/health", { signal });
  },

  getConnections(signal?: AbortSignal): Promise<ConnectionListResponse> {
    return requestJson<ConnectionListResponse>("/api/v1/connections", { signal });
  },

  getSchema(connectionId?: string, signal?: AbortSignal): Promise<SchemaIntrospectionResponse> {
    const params = new URLSearchParams();
    if (connectionId) params.set("connection_id", connectionId);
    const qs = params.toString();
    return requestJson<SchemaIntrospectionResponse>(`/api/v1/schema${qs ? `?${qs}` : ""}`, {
      signal,
    });
  },

  validateSql(payload: {
    sql: string;
    connection_id?: string;
    max_rows?: number;
  }): Promise<ValidateSQLResponse> {
    return requestJson<ValidateSQLResponse>("/api/v1/queries/validate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  executeSql(payload: {
    sql: string;
    connection_id?: string;
    max_rows?: number;
    include_explain?: boolean;
  }): Promise<ExecuteSQLResponse> {
    return requestJson<ExecuteSQLResponse>("/api/v1/queries/execute", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  async streamAskQuery(
    payload: {
      question: string;
      connection_id?: string;
      max_rows?: number;
      include_explain?: boolean;
    },
    handlers: StreamAskHandlers,
    signal?: AbortSignal,
  ): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/queries/ask/stream`, {
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      const detail = await parseErrorDetail(response);
      throw new ApiClientError(detail, response.status, detail);
    }

    if (!response.body) {
      throw new ApiClientError("Streaming response body was unavailable.", 500);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        buffer = buffer.replaceAll("\r\n", "\n");

        let boundary = buffer.indexOf("\n\n");
        while (boundary !== -1) {
          const block = buffer.slice(0, boundary);
          buffer = buffer.slice(boundary + 2);
          dispatchSseBlock(block, handlers);
          boundary = buffer.indexOf("\n\n");
        }
      }

      if (buffer.trim()) {
        dispatchSseBlock(buffer, handlers);
      }
    } finally {
      reader.releaseLock();
    }
  },

  getHistory(
    params: HistoryQueryParams = {},
    signal?: AbortSignal,
  ): Promise<QueryRunHistoryResponse> {
    const qs = new URLSearchParams();
    if (params.connection_id) qs.set("connection_id", params.connection_id);
    if (params.mode) qs.set("mode", params.mode);
    if (params.security_status) qs.set("security_status", params.security_status);
    if (params.execution_status) qs.set("execution_status", params.execution_status);
    if (params.search?.trim()) qs.set("search", params.search.trim());
    if (params.limit !== undefined) qs.set("limit", String(params.limit));
    if (params.offset !== undefined) qs.set("offset", String(params.offset));
    const query = qs.toString();
    return requestJson<QueryRunHistoryResponse>(`/api/v1/history${query ? `?${query}` : ""}`, {
      signal,
    });
  },

  getHistoryDetail(runId: string, signal?: AbortSignal): Promise<QueryRunHistoryDetail> {
    return requestJson<QueryRunHistoryDetail>(`/api/v1/history/${encodeURIComponent(runId)}`, {
      signal,
    });
  },

  getAnalytics(
    connectionId?: string,
    days = 14,
    signal?: AbortSignal,
  ): Promise<AnalyticsDashboardResponse> {
    const qs = new URLSearchParams({ days: String(days) });
    if (connectionId) qs.set("connection_id", connectionId);
    return requestJson<AnalyticsDashboardResponse>(`/api/v1/analytics?${qs.toString()}`, {
      signal,
    });
  },

  getEvalCases(difficulty?: string, signal?: AbortSignal): Promise<GoldenTestCase[]> {
    const qs = difficulty ? `?difficulty=${encodeURIComponent(difficulty)}` : "";
    return requestJson<GoldenTestCase[]>(`/api/v1/evals/cases${qs}`, { signal });
  },

  getLatestEvalRun(signal?: AbortSignal): Promise<EvalRunResponse> {
    return requestJson<EvalRunResponse>("/api/v1/evals/latest", { signal });
  },

  getEvalHistory(signal?: AbortSignal): Promise<EvalRunSummary[]> {
    return requestJson<EvalRunSummary[]>("/api/v1/evals/history", { signal });
  },

  runBenchmark(payload: EvalRunRequest): Promise<EvalRunResponse> {
    return requestJson<EvalRunResponse>("/api/v1/evals/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  generateScenario(payload: ScenarioGenerateRequest): Promise<ScenarioGenerateResponse> {
    return requestJson<ScenarioGenerateResponse>("/api/v1/scenarios/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  resetDatabaseScenario(): Promise<ScenarioResetResponse> {
    return requestJson<ScenarioResetResponse>("/api/v1/scenarios/reset", {
      method: "POST",
    });
  },

  getEvalLapsSummary(windowDays = 30, signal?: AbortSignal): Promise<EvalLapsSummary> {
    return requestJson<EvalLapsSummary>(`/api/v1/evallaps/summary?window_days=${windowDays}`, { signal });
  },

  getEvalLapsProviders(windowDays = 30, signal?: AbortSignal): Promise<ProviderUsageSummary[]> {
    return requestJson<ProviderUsageSummary[]>(`/api/v1/evallaps/providers?window_days=${windowDays}`, { signal });
  },

  getEvalLapsStages(windowDays = 30, signal?: AbortSignal): Promise<StageUsageSummary[]> {
    return requestJson<StageUsageSummary[]>(`/api/v1/evallaps/stages?window_days=${windowDays}`, { signal });
  },

  getEvalLapsRunTokens(runId: string, signal?: AbortSignal): Promise<TokenLedgerItem[]> {
    return requestJson<TokenLedgerItem[]>(`/api/v1/evallaps/runs/${runId}`, { signal });
  },

  getEvalLapsRenewals(signal?: AbortSignal): Promise<ProviderRenewalMeta[]> {
    return requestJson<ProviderRenewalMeta[]>("/api/v1/evallaps/renewals", { signal });
  },
};
