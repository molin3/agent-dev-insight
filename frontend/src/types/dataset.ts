export interface Dataset {
  id: string;
  name: string;
  description?: string;
  version: number;
  created_at: string;
}

export interface DatasetItem {
  id: string;
  dataset_id: string;
  input: Record<string, unknown>;
  expected_output?: string;
  eval_criteria?: string;
  source_trace_id?: string;
}
