// about the collections component
// this component shows the list of collections retrieved from the backend api
// it allows creating new collections and deleting existing ones
// when a collection is clicked, it calls onSelectCollection callback to notify parent component
// this component is important because collections are the top-level organisational unit for datasets and analysis runs
// collections is the UI component that manages and displays user collections of datasets.
// it uses the api functions defined in api/collections.ts to interact with the backend
// to fetch, create, and delete collections.
// collections.tsx is the frontend component that handles displaying and managing collections in the UI.
// it is the starting point for users to organise their datasets for analysis.
// it transforms user actions into API calls and updates the UI accordingly.
// collections is the bridge between user collection management actions and backend data storage.

import { useEffect, useState } from "react";
import type { Collection as ApiCollection } from "./api/collections";
import { getCollections, createCollection, deleteCollection } from "./api/collections";

interface CollectionsProps {
  onSelectCollection?: (collection: ApiCollection) => void;
  searchQuery: string;
}

export default function Collections({ onSelectCollection, searchQuery }: CollectionsProps) {
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

  const filteredCollections = collections.filter((collection) =>
    collection.name.toLowerCase().includes(searchQuery.toLowerCase().trim()),
  );

  return (
    <section className="screen page-collections">
      <section className="hero-block">
        <div>
          <h2>Collections</h2>
          <p className="hero-text">Create, review, and open saved collections.</p>
        </div>
      </section>

      <section className="flow-section search-create-strip">
        <div className="section-header-row compact-row">
          <h3 className="section-title">Create Collection</h3>
          <form onSubmit={handleCreate} className="form-inline create-row">
            <input
              className="form-input"
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Collection name"
              name="collectionName"
            />
            <button type="submit" className="btn btn-primary" disabled={creating}>
              {creating ? "Creating..." : "Create"}
            </button>
          </form>
        </div>
        {error && <p className="inline-error">{error}</p>}
      </section>

      <section className="flow-section flow-stretch">
        <div className="section-header-row">
          <div>
            <p className="section-kicker">Directory</p>
            <h3 className="section-title">All Collections</h3>
          </div>
        </div>

        {filteredCollections.length === 0 ? (
          <div className="empty-state">
            <h3>{collections.length === 0 ? "No collections yet" : "No matching collections"}</h3>
            <p>{collections.length === 0 ? "Create a collection to begin." : "Try a different search."}</p>
          </div>
        ) : (
          <div className="entity-list" aria-label="Collections">
            {filteredCollections.map((collection) => (
              <article
                key={collection.id}
                className="entity-row entity-row-inline clickable"
                onClick={() => onSelectCollection?.(collection)}
                title="Open collection"
              >
                <div className="entity-main">
                  <span className="entity-title">{collection.name}</span>
                </div>
                <span className="entity-date">{new Date(collection.created_at).toLocaleDateString()}</span>
                <div className="entity-actions">
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={(e) => handleDelete(e, collection.id)}
                    title="Delete collection"
                    aria-label={`Delete ${collection.name}`}
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}
