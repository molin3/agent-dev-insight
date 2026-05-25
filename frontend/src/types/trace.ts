export interface Trace {
  id: string;
  project_id: string;
  name: string;
  user_id?: string;
  session_id?: string;
  tags?: string[];
  extra_metadata?: Record<string, unknown>;
  status: "in_progress" | "completed" | "error";
  release?: string;
  version?: string;
  started_at?: string;
  completed_at?: string;
  total_latency_ms?: number;
  total_tokens?: number;
  total_cost?: number;
  error_message?: string;
  spans?: Span[];
  scores?: Score[];
}

export interface Span {
  id: string;
  trace_id: string;
  parent_span_id?: string;
  name: string;
  type: "llm" | "tool" | "retriever" | "embedding" | "agent" | "span";
  model?: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  extra_metadata?: Record<string, unknown>;
  status: "in_progress" | "completed" | "error";
  started_at?: string;
  ended_at?: string;
  latency_ms?: number;
  usage?: Record<string, number>;
  cost?: number;
  error_message?: string;
  level: number;
  generations?: Generation[];
}

export interface Generation {
  id: string;
  span_id?: string;
  model: string;
  prompt?: unknown[];
  completion?: string;
  usage?: Record<string, number>;
  cost?: number;
  latency_ms?: number;
  extra_metadata?: Record<string, unknown>;
}

export interface Score {
  id: string;
  trace_id: string;
  span_id?: string;
  name: string;
  value: number;
  comment?: string;
}

export interface TraceDetail extends Trace {
  spans: Span[];
  scores: Score[];
}

export interface ReplayEvent {
  timestamp: string;
  type: string;
  name?: string;
  model?: string;
  prompt?: unknown[];
  completion?: string;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  usage?: Record<string, number>;
  cost?: number;
  status?: string;
  latency_ms?: number;
}
