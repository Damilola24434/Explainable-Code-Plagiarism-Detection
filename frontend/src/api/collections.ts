// simple API client using fetch, no external libraries
// about collections it is the frontend API helper for data operations.
// it contins funtions the UI calls to talkto backend endpoits for collections,datasets, datasets files,singl file contet, ZIP upload
// it hes instead of writing fetch logic in every react componeents this file keeps all thoses API calls in one place
// why it matters is because reactpages use this fie to send user actios to the backedn
// backend routes then save / read frthe databse.  so this file is the frontend to backend bridge for collection/datset/file features
// so the collections.ts is the fri=ontend network layer that handels collecions- related API featurees.
export interface Collection {
  id: string;
  owner_id: string;
  name: string;
  created_at: string;
}

export interface Dataset {
  id: string;
  collection_id: string;
  name: string;
  created_at: string;
}

export interface FileData {
  id: string;
  submission_id: string;
  path: string;
  storage_key: string;
}

export interface UploadSkippedFile {
  path: string;
  reason: string;
}

export interface UploadDatasetSummary {
  message: string;
  dataset_id: string;
  stored_files: number;
  skipped_files: number;
  skipped: UploadSkippedFile[];
  language_counts: Record<string, number>;
  warnings: string[];
}

const API_BASE = "/api";
const COLLECTIONS_BASE = `${API_BASE}/collections/`;

async function readErrorMessage(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    if (data.detail?.message) return data.detail.message;
  } catch {
    // fall through to fallback
  }
  return fallback;
}

export async function getCollections(): Promise<Collection[]> {
  const res = await fetch(COLLECTIONS_BASE);
  if (!res.ok) throw new Error("Failed to fetch collections");
  return res.json();
}

export async function createCollection(name: string): Promise<Collection> {
  const res = await fetch(COLLECTIONS_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Failed to create collection");
  return res.json();
}

export async function updateCollection(id: string, name: string): Promise<Collection> {
  const res = await fetch(`${COLLECTIONS_BASE}${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Failed to update collection");
  return res.json();
}

export async function deleteCollection(id: string): Promise<void> {
  const res = await fetch(`${COLLECTIONS_BASE}${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete collection");
}

// datasets
export async function getDatasets(collectionId: string): Promise<Dataset[]> {
  const res = await fetch(`${API_BASE}/datasets/?collection_id=${encodeURIComponent(collectionId)}`);
  if (!res.ok) throw new Error("Failed to fetch datasets");
  return res.json();
}

export async function uploadDatasetZip(collectionId: string, zip: File): Promise<UploadDatasetSummary> {
  const form = new FormData();
  form.append("file", zip);
  const res = await fetch(`${COLLECTIONS_BASE}${collectionId}/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(await readErrorMessage(res, "Failed to upload zip"));
  return res.json();
}

export async function deleteDataset(datasetId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/datasets/${datasetId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete dataset");
}

// files
export async function getFiles(datasetId: string): Promise<FileData[]> {
  const res = await fetch(`${API_BASE}/datasets/${datasetId}/files`);
  if (!res.ok) {
    const errorText = await res.text();
    console.error("Backend error response:", res.status, errorText);
    throw new Error(`Failed to fetch files (${res.status}): ${errorText}`);
  }
  return res.json();
}

export async function getFile(fileId: string): Promise<Response> {
  return fetch(`${API_BASE}/files/${fileId}`);
}
