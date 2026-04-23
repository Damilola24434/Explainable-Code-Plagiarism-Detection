// about analysis results page
// this is a react component that displays plagiarism analysis results in a clean way
// it shows similarity scores between file pairs, risk level from high, medium, low
// it shows matched file names and a visual side-by-side code comparison view.
//
// NAVIGATION FIX:
// When opening comparison, we push TWO history entries: first view:"results" then
// view:"comparison" on top. This means pressing back always lands on view:"results"
// which the popstate listener catches and closes the comparison view correctly.
// This prevents the back button from skipping past the results list to the dataset.
import { useEffect, useState } from "react";
import { getRunResults, getRunExportPdfUrl, type SimilarityResult } from "./api/runs";
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
  if (risk === "HIGH") return "#E07A5F";
  if (risk === "MEDIUM") return "#9f8458";
  return "#0F3D3E";
}

function sortRows(rows: SimilarityResult[], sortBy: "similarity" | "file_a") {
  return [...rows].sort((a, b) => {
    if (sortBy === "similarity") return b.similarity - a.similarity;
    return a.file_a.localeCompare(b.file_a);
  });
}

function countRisk(rows: SimilarityResult[], risk: "HIGH" | "MEDIUM" | "LOW") {
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
    loadResults();
  }, [runId]);

  // ✅ Back button handling (clean)
  useEffect(() => {
    const handlePopState = (event: PopStateEvent) => {
      const state = event.state as { view?: string } | null;

      if (state?.view !== "comparison") {
        setSelectedRow(null);
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Breadcrumbs
  useEffect(() => {
    const items: NavItem[] = [
      { label: "Collections", onClick: onBackToCollections },
      { label: collectionName, onClick: onBack },
      {
        label: datasetName,
        active: !selectedRow,
        onClick: selectedRow
          ? () => {
              setSelectedRow(null);
              window.history.back(); // ✅ correct
            }
          : undefined,
      },
    ];

    if (selectedRow) {
      items.push({ label: "Comparison", active: true });
    }

    onNavChange?.(items);
  }, [collectionName, datasetName, onBack, onBackToCollections, onNavChange, selectedRow]);

  // 🔥 COMPARISON VIEW
  if (selectedRow) {
    return (
      <SideBySideComparison
        runId={runId}
        pairId={selectedRow.id}
        fileAId={selectedRow.file_a_id}
        fileBId={selectedRow.file_b_id}
        fileAName={selectedRow.file_a}
        fileBName={selectedRow.file_b}
        similarity={selectedRow.similarity}
        datasetName={datasetName}
        onBack={() => {
          window.history.back(); // ✅ FIXED
        }}
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
          <label className="form-label">Sort</label>
          <select
            className="form-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "similarity" | "file_a")}
          >
            <option value="similarity">Similarity</option>
            <option value="file_a">File Name</option>
          </select>

          <button
            type="button"
            className="btn btn-secondary"
            style={{
              marginLeft: "auto",
              color: "#000",
              backgroundColor: "#fff",
              borderColor: "#ccc",
            }}
            onClick={() => window.open(getRunExportPdfUrl(runId), "_blank")}
          >
            Download PDF Report
          </button>
        </div>

        <div className="results-table">
          <div className="results-head">
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
                onClick={() => {
                  // 🔥 FIXED: only ONE pushState
                  window.history.pushState(
                    { view: "comparison", pairId: row.id },
                    "",
                    window.location.pathname
                  );
                  setSelectedRow(row);
                }}
              >
                <span>{row.file_a}</span>
                <span>{row.file_b}</span>
                <span>{(row.similarity * 100).toFixed(1)}%</span>
                <span>{row.risk}</span>
              </button>
            ))}
          </div>
        </div>
      </section>
    </section>
  );
}