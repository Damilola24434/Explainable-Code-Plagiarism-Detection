// frontend/src/CollectionDetails.tsx
// collectiondetails.tsx is the frontend component that shows details of a selected collection.
// it displays the datasets in the collection, allows uploading new datasets via zip files,
// and lets users start analysis jobs on the datasets.
//
// NAVIGATION FIX:
// Each sub-view transition (dataset list → progress → results) now pushes its own
// history entry with a "view" property. A popstate listener inside this component
// handles back button presses for those sub-views, stepping back one level at a time.
// App.tsx ignores states with a "view" property so there is no conflict.
// "results" and "comparison" states are owned by AnalysisResults — this component
// ignores those popstate events so AnalysisResults can handle them without interference.

import { useEffect, useState } from "react";
import type { Collection, Dataset } from "./api/collections";
import { getDatasets, uploadDatasetZip, deleteDataset } from "./api/collections";
import { createRun, getDatasetRunHistory, type Run } from "./api/runs";
import AnalysisResults from "./AnalysisResults";
import JobProgress from "./JobProgress";

type NavItem = {
  label: string;
  onClick?: () => void;
  active?: boolean;
};

interface Props {
  collection: Collection;
  onBack: () => void;
  onNavChange?: (items: NavItem[]) => void;
  searchQuery: string;
}

export default function CollectionDetails({ collection, onBack, onNavChange, searchQuery }: Props) {
  const [datasetList, setDatasetList] = useState<Dataset[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedZip, setSelectedZip] = useState<File | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [showResultsPage, setShowResultsPage] = useState(false);
  const [showProgressPage, setShowProgressPage] = useState(false);
  const [activeRun, setActiveRun] = useState<Run | null>(null);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const [completedRunsByDataset, setCompletedRunsByDataset] = useState<Record<string, Run>>({});
  const [processingDatasetId, setProcessingDatasetId] = useState<string | null>(null);
  const [deletingDatasetId, setDeletingDatasetId] = useState<string | null>(null);

  const resetZipInput = () => {
    const input = document.getElementById("zip-upload") as HTMLInputElement | null;
    if (input) input.value = "";
  };

  const refreshDatasets = async () => {
    try {
      const items = await getDatasets(collection.id);
      setDatasetList(items);

      const newCompletedRuns: Record<string, Run> = {};
      for (const dataset of items) {
        try {
          const runs = await getDatasetRunHistory(dataset.id);
          const completedRun = runs.find((run) => run.status === "DONE");
          if (completedRun) newCompletedRuns[dataset.id] = completedRun;
        } catch (err) {
          console.error(`Failed to load run history for dataset ${dataset.id}:`, err);
        }
      }
      setCompletedRunsByDataset(newCompletedRuns);
    } catch {
      console.error("load datasets");
    }
  };

  const closeRunViews = () => {
    // Return to dataset list
    setShowProgressPage(false);
    setShowResultsPage(false);
    setActiveRun(null);
    setActiveDatasetId(null);
  };

  const openProgressPage = (run: Run, datasetId: string) => {
    setActiveRun(run);
    setActiveDatasetId(datasetId);
    setProcessingDatasetId(datasetId);
    setShowProgressPage(true);
    setShowResultsPage(false);
    // Push history so back button can return to dataset list from progress
    window.history.pushState(
      { view: "progress", datasetId, collectionId: collection.id },
      "",
      window.location.pathname
    );
  };

  const openResultsPage = () => {
    if (activeRun && activeDatasetId) {
      setCompletedRunsByDataset((prev) => ({ ...prev, [activeDatasetId]: activeRun }));
    }
    setProcessingDatasetId(null);
    setShowProgressPage(false);
    setShowResultsPage(true);
    // Push history so back button can return to dataset list from results
    window.history.pushState(
      { view: "results", datasetId: activeDatasetId, collectionId: collection.id },
      "",
      window.location.pathname
    );
  };

  const openStoredResults = (datasetId: string) => {
    const run = completedRunsByDataset[datasetId];
    if (!run) return;
    setActiveRun(run);
    setActiveDatasetId(datasetId);
    setShowProgressPage(false);
    setShowResultsPage(true);
    // Push history so back button can return to dataset list from stored results
    window.history.pushState(
      { view: "results", datasetId, collectionId: collection.id },
      "",
      window.location.pathname
    );
  };

  // Handle browser back button for sub-views inside this component.
  // "results" and "comparison" are owned by AnalysisResults — ignore them here.
  // Only handle "progress" or no-view states to return to the dataset list.
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      const state = event.state as {
        view?: string;
        collectionId?: string;
        selectedCollection?: unknown;
      } | null;

      // These states belong to AnalysisResults — do not interfere
      if (state?.view === "results" || state?.view === "comparison") return;

      // "progress" or no view — return to dataset list
      if (!state?.view || state.view === "progress") {
        closeRunViews();
        return;
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    refreshDatasets();
  }, [collection]);

  const performUpload = async (file: File) => {
    if (!file || isUploading) return;
    setIsUploading(true);
    setUploadError(null);
    try {
      await uploadDatasetZip(collection.id, file);
      setSelectedZip(null);
      resetZipInput();
      const items = await getDatasets(collection.id);
      setDatasetList(items);
    } catch {
      console.error("upload zip");
      setUploadError("Upload failed. Please check the file and try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const runJob = async (datasetId: string) => {
    try {
      setRunError(null);
      const run = await createRun({ dataset_id: datasetId, config_json: {} });
      openProgressPage(run, datasetId);
    } catch {
      console.error("start run");
      setRunError("Failed to start analysis. Please try again.");
    }
  };

  const handleDeleteDataset = async (datasetId: string) => {
    if (!window.confirm("Are you sure you want to delete this dataset? This action cannot be undone.")) {
      return;
    }
    setDeletingDatasetId(datasetId);
    try {
      await deleteDataset(datasetId);
      setDatasetList((prev) => prev.filter((d) => d.id !== datasetId));
      setRunError(null);
    } catch {
      console.error("delete dataset");
      setRunError("Failed to delete dataset. Please try again.");
    } finally {
      setDeletingDatasetId(null);
    }
  };

  const filteredDatasets = datasetList.filter((dataset) =>
    dataset.name.toLowerCase().includes(searchQuery.toLowerCase().trim())
  );

  const activeDatasetName = activeDatasetId
    ? datasetList.find((dataset) => dataset.id === activeDatasetId)?.name ?? "Current Dataset"
    : "Current Dataset";

  // Update breadcrumb nav whenever the active sub-view changes
  useEffect(() => {
    const returnToCollections = () => {
      closeRunViews();
      onBack();
    };

    if (showProgressPage && activeRun) {
      onNavChange?.([
        { label: "Collections", onClick: returnToCollections },
        { label: collection.name, onClick: closeRunViews },
        { label: activeDatasetName, onClick: closeRunViews },
        { label: "Run", active: true },
      ]);
      return;
    }

    if (showResultsPage && activeRun) {
      onNavChange?.([
        { label: "Collections", onClick: returnToCollections },
        { label: collection.name, onClick: closeRunViews },
        { label: activeDatasetName, onClick: closeRunViews },
        { label: "Results", active: true },
      ]);
      return;
    }

    onNavChange?.([
      { label: "Collections", onClick: onBack },
      { label: collection.name, active: true },
    ]);
  }, [activeDatasetName, activeRun, collection.name, onBack, onNavChange, showProgressPage, showResultsPage]);

  if (showProgressPage && activeRun) {
    return (
      <section className="screen page-details">
        <JobProgress
          runId={activeRun.id}
          onComplete={openResultsPage}
          onCancel={() => setShowProgressPage(false)}
        />
      </section>
    );
  }

  if (showResultsPage && activeRun) {
    return (
      <section className="screen page-details">
        <AnalysisResults
          runId={activeRun.id}
          datasetName={activeDatasetName}
          collectionName={collection.name}
          onBack={closeRunViews}
          onBackToCollections={onBack}
          onNavChange={onNavChange}
        />
      </section>
    );
  }

  return (
    <section className="screen page-details">
      <div className="page-header workspace-header">
        <div>
          <h2>{collection.name}</h2>
        </div>
      </div>

      <section className="flow-section upload-section-compact top-upload-section">
        <div className="upload-strip">
          <h3 className="section-title">Upload Dataset</h3>
          <div className="upload-zone upload-inline">
            <input
              type="file"
              accept=".zip"
              id="zip-upload"
              style={{ display: "none" }}
              onChange={(e) => {
                const file = e.target.files ? e.target.files[0] : null;
                if (file) {
                  setSelectedZip(file);
                  setUploadError(null);
                  performUpload(file);
                }
              }}
            />
            <label htmlFor="zip-upload" className="btn btn-secondary file-picker-label">
              Choose File
            </label>
            {isUploading && <span className="upload-status">Uploading...</span>}
          </div>
        </div>
        {selectedZip && <span className="file-name top-file-name">{selectedZip.name}</span>}
        {uploadError && <div className="alert alert-error mt-1">{uploadError}</div>}
      </section>

      <section className="flow-section datasets-section-compact">
        <div className="section-header-row"></div>

        {runError && <div className="alert alert-error">{runError}</div>}

        {filteredDatasets.length === 0 ? (
          <div className="empty-state compact-empty-state">
            <h3>{datasetList.length === 0 ? "No datasets yet" : "No matching datasets"}</h3>
            <p>{datasetList.length === 0 ? "Upload a ZIP file to begin." : "Try a different search."}</p>
          </div>
        ) : (
          <div className="entity-list" aria-label="Datasets">
            {filteredDatasets.map((d) => {
              const isProcessing = processingDatasetId === d.id;
              const isCompleted = completedRunsByDataset[d.id];
              const isDisabled = processingDatasetId !== null && !isProcessing;

              return (
                <article
                  key={d.id}
                  className={`entity-row entity-row-inline ${isProcessing ? "processing" : ""} ${isCompleted ? "completed" : ""}`}
                >
                  {isProcessing && (
                    <div className="status-indicator processing">
                      <span className="spinner"></span>
                    </div>
                  )}
                  {isCompleted && (
                    <div className="status-indicator completed">
                      <span className="checkmark">✓</span>
                    </div>
                  )}
                  <div className="entity-main">
                    <span className="entity-title">{d.name}</span>
                    {isProcessing && <span className="status-text">Analyzing...</span>}
                    {isCompleted && <span className="status-text">Complete</span>}
                  </div>
                  <span className="entity-date">{new Date(d.created_at).toLocaleDateString()}</span>
                  <div className="entity-actions">
                    {isCompleted ? (
                      <button
                        className="btn btn-primary dataset-action-btn"
                        onClick={() => openStoredResults(d.id)}
                      >
                        View Results
                      </button>
                    ) : isProcessing ? (
                      <span className="btn btn-disabled dataset-action-btn">Processing...</span>
                    ) : (
                      <button
                        className="btn btn-primary dataset-action-btn"
                        onClick={() => runJob(d.id)}
                        disabled={isDisabled}
                        title={isDisabled ? "Wait for current analysis to finish" : ""}
                      >
                        Run Analysis
                      </button>
                    )}
                    <button
                      className="btn btn-danger dataset-action-btn"
                      onClick={() => handleDeleteDataset(d.id)}
                      disabled={deletingDatasetId === d.id || isProcessing}
                      title={isProcessing ? "Cannot delete while processing" : "Delete this dataset"}
                    >
                      {deletingDatasetId === d.id ? "Deleting..." : "Delete"}
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </section>
  );
}