// about analysis results page
// this is a react component that displays plagiarism anayiss results in a clean way
// it shows simpilarity scores between file pairs, risk level from high. medium-low
// it shows matched file names, it shows a visual comparison /sise by side code view.
// it fetches the run reult from the the backend processing usinf API then it formart  and display them in the UI
// this code file matters because this is the final results screen user see after run analuysis complates.
// it transforms raw results/data int readable report
// analysis results is the UI component that displays plagiarism detection results to the user.


import { useEffect, useState } from "react";
import { getRunResults, type SimilarityResult } from "./api/runs";
import SideBySideComparison from "./SideBySideComparison";

type NavItem = {
  label: string;
  onClick?: () => void;
  active?: boolean;
};

interface Props {
  runId: string;
  datasetName: string;
  collectionName: string;
  onBack: () => void;
  onBackToCollections: () => void;
  onNavChange?: (items: NavItem[]) => void;
}

function getRiskColor(risk: string): string {
  // set risk color
  if (risk === "HIGH") return "#E07A5F";
  if (risk === "MEDIUM") return "#9f8458";
  return "#0F3D3E";
}

function sortRows(rows: SimilarityResult[], sortBy: "similarity" | "file_a") {
  // sort result rows
  return [...rows].sort((a, b) => {
    if (sortBy === "similarity") return b.similarity - a.similarity;
    return a.file_a.localeCompare(b.file_a);
  });
}

function countRisk(rows: SimilarityResult[], risk: "HIGH" | "MEDIUM" | "LOW") {
  // count risk rows
  return rows.filter((row) => row.risk === risk).length;
}

export default function AnalysisResults({
  runId,
  datasetName,
  collectionName,
  onBack,
  onBackToCollections,
  onNavChange,
}: Props) {
  const [resultRows, setResultRows] = useState<SimilarityResult[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"similarity" | "file_a">("similarity");
  const [selectedRow, setSelectedRow] = useState<SimilarityResult | null>(null);

  const loadResults = async () => {
    // fetch results from api
    setIsLoading(true);
    setLoadError(null);
    try {
      const rows = await getRunResults(runId);
      setResultRows(rows);
    } catch (error) {
      console.error("load results", error);
      setLoadError("Failed to load results.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // load when run changes
    loadResults();
  }, [runId]);

  useEffect(() => {
    const items: NavItem[] = [
      { label: "Collections", onClick: onBackToCollections },
      { label: collectionName, onClick: onBack },
      { label: datasetName, onClick: onBack },
      selectedRow
        ? { label: "Results", onClick: () => setSelectedRow(null) }
        : { label: "Results", active: true },
    ];

    if (selectedRow) {
      items.push({ label: "Comparison", active: true });
    }

    onNavChange?.(items);
  }, [collectionName, datasetName, onBack, onBackToCollections, onNavChange, selectedRow]);

  if (selectedRow) {
    return (
      <SideBySideComparison
        fileAId={selectedRow.file_a_id}
        fileBId={selectedRow.file_b_id}
        fileAName={selectedRow.file_a}
        fileBName={selectedRow.file_b}
        similarity={selectedRow.similarity}
        datasetName={datasetName}
        onBack={() => setSelectedRow(null)}
      />
    );
  }

  if (isLoading) return <div className="loading">Loading results...</div>;

  if (loadError) {
    return (
      <section className="flow-section">
        <div className="alert alert-error">{loadError}</div>
      </section>
    );
  }

  const sortedRows = sortRows(resultRows, sortBy);
  const highCount = countRisk(resultRows, "HIGH");
  const mediumCount = countRisk(resultRows, "MEDIUM");
  const lowCount = countRisk(resultRows, "LOW");

  return (
    <section className="screen page-results">
      <div className="page-header">
        <div>
          <p className="section-kicker">Results</p>
          <h2>Analysis Results</h2>
          <p className="page-subtitle">Review flagged file pairs.</p>
        </div>
      </div>

      <div className="stats-row results-summary-row">
        <div className="stat-card">
          <div className="stat-label">Total</div>
          <div className="stat-value">{resultRows.length}</div>
        </div>
        <div className="stat-card danger">
          <div className="stat-label">High</div>
          <div className="stat-value">{highCount}</div>
        </div>
        <div className="stat-card warning">
          <div className="stat-label">Medium</div>
          <div className="stat-value">{mediumCount}</div>
        </div>
        <div className="stat-card success">
          <div className="stat-label">Low</div>
          <div className="stat-value">{lowCount}</div>
        </div>
      </div>

      <section className="flow-section">
        <div className="results-toolbar">
          <label className="form-label" htmlFor="results-sort">Sort</label>
          <select
            id="results-sort"
            className="form-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "similarity" | "file_a")}
          >
            <option value="similarity">Similarity</option>
            <option value="file_a">File Name</option>
          </select>
        </div>

        {resultRows.length === 0 ? (
          <div className="empty-state">
            <h3>No pairs found</h3>
            <p>Not enough files for comparison.</p>
          </div>
        ) : (
          <div className="results-table">
            <div className="results-head" aria-hidden="true">
              <span>File A</span>
              <span>File B</span>
              <span>Similarity</span>
              <span>Risk</span>
            </div>
            <div className="results-list">
              {sortedRows.map((row) => (
                <button
                  key={row.id}
                  type="button"
                  className="result-row"
                  onClick={() => setSelectedRow(row)}
                  title="Click to view side-by-side comparison"
                >
                  <span className="result-col result-file mono">{row.file_a}</span>
                  <span className="result-col result-file mono">{row.file_b}</span>
                  <span className="result-col result-score">
                    <span className={`result-percent risk-${row.risk.toLowerCase()}`}>
                      {(row.similarity * 100).toFixed(1)}%
                    </span>
                    <div className="sim-bar">
                      <div
                        className="sim-bar-fill"
                        style={{ width: `${row.similarity * 100}%`, background: getRiskColor(row.risk) }}
                      />
                    </div>
                  </span>
                  <span className={`result-col result-risk risk-${row.risk.toLowerCase()}`}>{row.risk}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    </section>
  );
}
// This file shows the final plagiarism results after a run is complete.
// It loads result data from the backend, sorts the matched file pairs,
// shows risk levels and similarity scores, and lets the user open a side by side comparison view.