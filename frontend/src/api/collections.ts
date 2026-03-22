// simple API client using fetch, no external libraries

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

const API_BASE = "/api";
const COLLECTIONS_BASE = `${API_BASE}/collections/`;

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

export async function uploadDatasetZip(collectionId: string, zip: File): Promise<void> {
  const form = new FormData();
  form.append("upload", zip);
  const res = await fetch(`${COLLECTIONS_BASE}${collectionId}/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Failed to upload zip");
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