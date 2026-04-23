// this file is the frontend API helper for anaysis runs.
// it has fuctios to start a run,check run status/progress, get run results
// the UI componenes call thus fie instead of writing fetch calls directly.
// why it matters is backend manges runs,
// this file is the frontend side that talks to that backend routes.
// so this files is what cnnets the run analysis buttin to acutual backend run processing/.
// runs is the frontend network layer for starting and tracking plagiarism analysis run procesing.
// runs.ts is the frontend netwoek layer for startig and trackin pagiarism analysis runs.


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

export interface MatchEvidence {
  id: string;
  run_id: string;
  file_a_id: string;
  file_b_id: string;
  a_start: number;
  a_end: number;
  b_start: number;
  b_end: number;
  kind: string;
  weight: number;
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  // call api
  const response = await fetch(url, init);
  if (!response.ok) {
    let message = `Request failed: ${response.status} ${response.statusText}`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (data.detail?.message) {
        message = data.detail.message;
      }
    } catch {
      // keep default message
    }
    throw new Error(message);
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

export async function getDatasetRunHistory(datasetId: string): Promise<Run[]> {
  // fetch all completed runs for a dataset
  return requestJson<Run[]>(`${API_BASE}/runs/dataset/${datasetId}/history`);
}

export async function getRunResults(runId: string): Promise<SimilarityResult[]> {
  // fetch run results
  return requestJson<SimilarityResult[]>(`${API_BASE}/runs/${runId}/results`);
}

export function getRunExportPdfUrl(runId: string): string {
  return `${API_BASE}/runs/${runId}/export-pdf`;
}

export async function getPairEvidence(runId: string, pairId: string): Promise<MatchEvidence[]> {
  return requestJson<MatchEvidence[]>(`${API_BASE}/runs/${runId}/results/${pairId}/evidence`);
}
