export interface Experiment {
  id: string;
  name: string;
  description?: string;
  task_description: string;
  dataset_id?: string;
  status: string;
  created_at: string;
  runs?: ExperimentRun[];
}

export interface ExperimentRun {
  id: string;
  experiment_id: string;
  model_name: string;
  provider: string;
  status: string;
  avg_latency_ms?: number;
  total_tokens?: number;
  total_cost?: number;
  completion_rate?: number;
}
