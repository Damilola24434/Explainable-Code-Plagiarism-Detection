import { useEffect, useState } from "react";
import type { Collection, Dataset } from "./api/collections";
import { getDatasets, uploadDatasetZip } from "./api/collections";
import { createRun, type Run } from "./api/runs";
import AnalysisResults from "./AnalysisResults";
import JobProgress from "./JobProgress";

interface Props {
  collection: Collection;
  onBack: () => void;
}

export default function CollectionDetails({ collection, onBack }: Props) {
  const [datasetList, setDatasetList] = useState<Dataset[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [selectedZip, setSelectedZip] = useState<File | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [showResultsPage, setShowResultsPage] = useState(false);
  const [showProgressPage, setShowProgressPage] = useState(false);
  const [activeRun, setActiveRun] = useState<Run | null>(null);

  const resetZipInput = () => {
    // clear file input value
    const input = document.getElementById("zip-upload") as HTMLInputElement | null;
    if (input) {
      input.value = "";
    }
  };

  const refreshDatasets = async () => {
    // load collection datasets
    try {
      const items = await getDatasets(collection.id);
      setDatasetList(items);
    } catch {
      console.error("load datasets");
    }
  };

  const openProgressPage = (run: Run) => {
    // show progress view
    setActiveRun(run);
    setShowProgressPage(true);
    setShowResultsPage(false);
  };

  const openResultsPage = () => {
    // show results view
    setShowProgressPage(false);
    setShowResultsPage(true);
  };

  const closeRunViews = () => {
    // go back to dataset list
    setShowProgressPage(false);
    setShowResultsPage(false);
    setActiveRun(null);
  };

  useEffect(() => {
    refreshDatasets();
  }, [collection]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedZip || isUploading) return;

    // start upload
    setIsUploading(true);
    setUploadError(null);

    try {
      await uploadDatasetZip(collection.id, selectedZip);
      setSelectedZip(null);
      resetZipInput();
      await refreshDatasets();
    } catch {
      console.error("upload zip");
      setUploadError("Upload failed. Please check the file and try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const runJob = async (datasetId: string) => {
    // start analysis job
    try {
      setRunError(null);
      const run = await createRun({ dataset_id: datasetId, config_json: {} });
      openProgressPage(run);
    } catch {
      console.error("start run");
      setRunError("Failed to start analysis. Please try again.");
    }
  };

  if (showProgressPage && activeRun) {
    return (
      <div>
        <div className="page-header">
          <button className="btn btn-secondary btn-sm" onClick={onBack}>← Collections</button>
          <h1>{collection.name}</h1>
        </div>
        <JobProgress
          runId={activeRun.id}
          onComplete={openResultsPage}
          onCancel={() => setShowProgressPage(false)}
        />
      </div>
    );
  }

  if (showResultsPage && activeRun) {
    return (
      <div>
        <div className="page-header">
          <button className="btn btn-secondary btn-sm" onClick={onBack}>← Collections</button>
          <h1>{collection.name}</h1>
        </div>
        <AnalysisResults
          runId={activeRun.id}
          onBack={closeRunViews}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <button className="btn btn-secondary btn-sm" onClick={onBack}>← Collections</button>
        <h1>{collection.name}</h1>
      </div>

      <div className="card mb-2">
        <div className="card-header">
          <h3 style={{ margin: 0 }}>Upload Submission Dataset</h3>
        </div>
        <div className="card-body">
          <p className="text-muted text-small mb-1">
            Upload a ZIP file containing student submissions. Each top-level folder represents one student.
          </p>
          <form onSubmit={handleUpload}>
            <div className="upload-zone">
              <input
                type="file"
                accept=".zip"
                id="zip-upload"
                style={{ display: "none" }}
                onChange={(e) => {
                  setSelectedZip(e.target.files ? e.target.files[0] : null);
                  setUploadError(null);
                }}
              />
              <label htmlFor="zip-upload" className="btn btn-secondary" style={{ cursor: "pointer" }}>
                Choose ZIP File
              </label>
              <span className="file-name">{selectedZip ? selectedZip.name : "No file selected"}</span>
              <button type="submit" className="btn btn-primary" disabled={!selectedZip || isUploading}>
                {isUploading ? "Uploading..." : "Upload Dataset"}
              </button>
            </div>
            {uploadError && <div className="alert alert-error mt-1">{uploadError}</div>}
          </form>
        </div>
      </div>

      <div className="page-header" style={{ marginTop: "1.5rem" }}>
        <h2>Datasets</h2>
      </div>

      {runError && <div className="alert alert-error">{runError}</div>}

      {datasetList.length === 0 ? (
        <div className="empty-state">
          <h3>No datasets yet</h3>
          <p>Upload a ZIP file above to create your first dataset.</p>
        </div>
      ) : (
        datasetList.map((d) => (
          <div key={d.id} className="dataset-card">
            <div className="dataset-card-header">
              <div>
                <div className="dataset-name">{d.name}</div>
                <div className="dataset-meta">
                  Added {new Date(d.created_at).toLocaleDateString()}
                </div>
              </div>
              <button className="btn btn-primary" onClick={() => runJob(d.id)}>
                Run Plagiarism Detection
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
