import { useEffect, useState } from "react";
import type { Collection as ApiCollection } from "./api/collections";
import { getCollections, createCollection, deleteCollection } from "./api/collections";

interface CollectionsProps {
  onSelectCollection?: (collection: ApiCollection) => void;
}

export default function Collections({ onSelectCollection }: CollectionsProps) {
  const [collections, setCollections] = useState<ApiCollection[]>([]);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string>("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadWithRetry();
  }, []);

  const load = async () => {
    try {
      const data = await getCollections();
      setCollections(data);
      setError("");
    } catch (err) {
      console.error("load collections", err);
      setError("Could not load collections. Check backend logs and try again.");
    }
  };

  const loadWithRetry = async () => {
    for (let attempt = 1; attempt <= 5; attempt += 1) {
      try {
        const data = await getCollections();
        setCollections(data);
        setError("");
        return;
      } catch (err) {
        console.error(`load collections attempt ${attempt}`, err);
        if (attempt === 5) {
          setError("Could not load collections. Check backend logs and try again.");
          return;
        }
        await new Promise((resolve) => setTimeout(resolve, 1500));
      }
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setCreating(true);
    setError("");
    try {
      await createCollection(input.trim());
      await load();
      setInput("");
    } catch (err) {
      console.error("create collection", err);
      setError(err instanceof Error ? err.message : "Failed to create collection.");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await deleteCollection(id);
      setCollections((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error("delete collection", err);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Collections</h1>
          <p className="text-muted text-small" style={{ marginTop: "0.25rem" }}>
            Organise student submission datasets into collections.
          </p>
        </div>
      </div>

      <div className="card mb-2">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>New Collection</h3>
        </div>
        <div className="card-body">
          <form onSubmit={handleCreate} className="form-inline">
            <input
              className="form-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter collection name"
              name="collectionName"
            />
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? "Creating..." : "Create"}
            </button>
          </form>
          {error && <p className="text-muted" style={{ color: "#b42318", marginTop: "0.75rem" }}>{error}</p>}
        </div>
      </div>

      {collections.length === 0 ? (
        <div className="empty-state">
          <h3>No collections yet</h3>
          <p>Create a collection above to get started.</p>
        </div>
      ) : (
        <div className="collection-list">
          {collections.map((collection) => (
            <div
              key={collection.id}
              className="collection-row"
              onClick={() => onSelectCollection?.(collection)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === "Enter" && onSelectCollection?.(collection)}
            >
              <div style={{ flex: 1 }}>
                <div className="collection-name">{collection.name}</div>
                <div className="collection-meta">
                  Created {new Date(collection.created_at).toLocaleDateString()}
                </div>
              </div>
              <button
                className="btn btn-ghost btn-sm"
                onClick={(e) => handleDelete(e, collection.id)}
                title="Delete collection"
                aria-label={`Delete ${collection.name}`}
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
