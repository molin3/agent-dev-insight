export interface DashboardOverview {
  total_traces: number;
  completed: number;
  errors: number;
  total_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
}
