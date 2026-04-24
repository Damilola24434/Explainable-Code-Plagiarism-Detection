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
import { getCollections, createCollection, deleteCollection, uploadDatasetZip } from "./api/collections";

interface CollectionsProps {
  onSelectCollection?: (collection: ApiCollection) => void;
  searchQuery: string;
}

export default function Collections({ onSelectCollection, searchQuery }: CollectionsProps) {
  const [collections, setCollections] = useState<ApiCollection[]>([]);
  const [error, setError] = useState<string>("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [collectionName, setCollectionName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    loadWithRetry();
  }, []);

  const load = async () => {
    try {
      const data = await getCollections();
      // Sort by created_at in reverse order (newest first)
      data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
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
        // Sort by created_at in reverse order (newest first)
        data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
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

  const handleCreateWithFile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!collectionName.trim()) {
      setError("Collection name is required.");
      return;
    }

    setIsCreating(true);
    setError("");

    try {
      // Create the collection
      const newCollection = await createCollection(collectionName.trim());
      
      // If a file was selected, upload it automatically
      if (selectedFile) {
        try {
          await uploadDatasetZip(newCollection.id, selectedFile);
        } catch (uploadErr) {
          console.error("auto-upload failed", uploadErr);
          // Collection was created, but upload failed - still navigate to it
          setError("Collection created, but file upload failed. You can retry uploading later.");
        }
      }

      // Navigate to the new collection
      onSelectCollection?.(newCollection);
      
      // Reset modal
      setShowCreateModal(false);
      setCollectionName("");
      setSelectedFile(null);
      
      // Refresh the collections list
      await load();
    } catch (err) {
      console.error("create collection with file", err);
      setError(err instanceof Error ? err.message : "Failed to create collection.");
    } finally {
      setIsCreating(false);
    }
  };

  const resetModal = () => {
    setShowCreateModal(false);
    setCollectionName("");
    setSelectedFile(null);
    setError("");
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
          <h3 className="section-title">Start New Collection</h3>
          <button 
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
          >
            + New Collection
          </button>
        </div>
      </section>

      <section className="flow-section flow-stretch">
        <div className="section-header-row">
          <div>
            <p className="section-kicker">Directory</p>
            <h3 className="section-title">All Collections</h3>
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

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
                    className="btn btn-danger"
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

      {/* Create Collection Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={resetModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create Collection</h2>
              <button 
                className="modal-close-btn"
                onClick={resetModal}
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateWithFile} className="modal-form">
              <div className="form-group">
                <label htmlFor="collection-name" className="form-label">Collection Name</label>
                <input
                  id="collection-name"
                  className="form-input"
                  type="text"
                  value={collectionName}
                  onChange={(e) => setCollectionName(e.target.value)}
                  placeholder="Enter collection name"
                  autoFocus
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="zip-file" className="form-label">Upload ZIP File (Optional)</label>
                <p className="form-helper">Upload a ZIP file to immediately start analysis</p>
                <input
                  id="zip-file"
                  type="file"
                  accept=".zip"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="form-file-input"
                />
                {selectedFile && (
                  <div className="file-selected">
                    <span className="file-icon">📎</span>
                    <span className="file-name">{selectedFile.name}</span>
                    <button
                      type="button"
                      className="btn-remove-file"
                      onClick={() => setSelectedFile(null)}
                      aria-label="Remove file"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>

              {error && <div className="alert alert-error">{error}</div>}

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={resetModal}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isCreating || !collectionName.trim()}
                >
                  {isCreating ? "Creating..." : "Create Collection"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}
