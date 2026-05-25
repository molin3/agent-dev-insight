const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.detail || err.message || "Request failed");
  }
  const body = await res.json();
  return body.data as T;
}

// Trace API
export const traceApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ total: number; items: Trace[] }>(`/traces${qs}`);
  },
  get: (id: string) => request<TraceDetail>(`/traces/${id}`),
  delete: (id: string) => request<null>(`/traces/${id}`, { method: "DELETE" }),
  complete: (id: string) => request<Trace>(`/traces/${id}/complete`, { method: "POST" }),
  replay: (id: string) => request<{ events: ReplayEvent[] }>(`/traces/${id}/replay`),
  evaluate: (id: string, evaluatorNames?: string[]) =>
    request<{ score_count: number; scores: Score[] }>(`/traces/${id}/evaluate`, {
      method: "POST",
      body: JSON.stringify({ evaluator_names: evaluatorNames }),
    }),
  scores: (id: string) => request<{ scores: Score[] }>(`/traces/${id}/scores`),
};

// Dashboard API
export const dashboardApi = {
  overview: () => request<DashboardOverview>("/dashboard/overview"),
};

// Dataset API
export const datasetApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ total: number; items: Dataset[] }>(`/datasets${qs}`);
  },
  get: (id: string) => request<{ dataset: Dataset; items: DatasetItem[] }>(`/datasets/${id}`),
  create: (data: { name: string; description?: string }) =>
    request<Dataset>("/datasets", { method: "POST", body: JSON.stringify(data) }),
  delete: (id: string) => request<null>(`/datasets/${id}`, { method: "DELETE" }),
  addItem: (id: string, item: { input: Record<string, unknown>; expected_output?: string }) =>
    request<DatasetItem>(`/datasets/${id}/items`, {
      method: "POST",
      body: JSON.stringify(item),
    }),
};

// Experiment API
export const experimentApi = {
  list: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<{ total: number; items: Experiment[] }>(`/experiments${qs}`);
  },
  get: (id: string) => request<{ experiment: Experiment; comparison: unknown; runs: ExperimentRun[] }>(
    `/experiments/${id}`
  ),
  create: (data: { name: string; task_description: string; description?: string }) =>
    request<Experiment>("/experiments", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  run: (id: string) => request<Experiment>(`/experiments/${id}/run`, { method: "POST" }),
  delete: (id: string) => request<null>(`/experiments/${id}`, { method: "DELETE" }),
};

// Types (imported from types/)
import type { Trace, Score } from "@/types/trace";
import type { TraceDetail, ReplayEvent } from "@/types/trace";
import type { DashboardOverview } from "@/types/dashboard";
import type { Dataset, DatasetItem } from "@/types/dataset";
import type { Experiment, ExperimentRun } from "@/types/experiment";
