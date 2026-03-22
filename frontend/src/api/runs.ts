const API_BASE = "/api";

export interface Run {
  id: string;
  dataset_id: string;
  status: "QUEUED" | "RUNNING" | "DONE" | "FAILED";
  stage: "INGEST" | "TOKENS" | "AST" | "REPORT";
  progress_pct: number;
  config_json: Record<string, unknown>;
  error_message?: string;
  created_at: string;
  started_at?: string;
  finished_at?: string;
  completed_at?: string;
}

export interface SimilarityResult {
  id: string;
  file_a: string;
  file_b: string;
  file_a_id: string;
  file_b_id: string;
  similarity: number;   // 0.0 – 1.0
  risk: "HIGH" | "MEDIUM" | "LOW";
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  // call api
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }

  // parse json
  return response.json() as Promise<T>;
}

export async function createRun(payload: {
  dataset_id: string;
  config_json?: Record<string, unknown>;
}): Promise<Run> {
  // start analysis job
  return requestJson<Run>(`${API_BASE}/runs/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      dataset_id: payload.dataset_id,
      config_json: payload.config_json ?? {},
    }),
  });
}

export async function getRun(runId: string): Promise<Run> {
  // get run status
  return requestJson<Run>(`${API_BASE}/runs/${runId}`);
}

export async function getRunResults(runId: string): Promise<SimilarityResult[]> {
  // fetch run results
  return requestJson<SimilarityResult[]>(`${API_BASE}/runs/${runId}/results`);
}