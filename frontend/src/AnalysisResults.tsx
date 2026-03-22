import { useEffect, useState } from "react";
import { getRunResults, type SimilarityResult } from "./api/runs";
import SideBySideComparison from "./SideBySideComparison";

interface Props {
  runId: string;
  onBack: () => void;
}

function getRiskColor(risk: string): string {
  // set risk color
  if (risk === "HIGH") return "var(--danger)";
  if (risk === "MEDIUM") return "var(--warning)";
  return "var(--success)";
}

function getRiskBadgeClass(risk: string): string {
  // set risk badge style
  if (risk === "HIGH") return "badge badge-high";
  if (risk === "MEDIUM") return "badge badge-medium";
  return "badge badge-low";
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

export default function AnalysisResults({ runId, onBack }: Props) {
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

  if (selectedRow) {
    return (
      <SideBySideComparison
        fileAId={selectedRow.file_a_id}
        fileBId={selectedRow.file_b_id}
        fileAName={selectedRow.file_a}
        fileBName={selectedRow.file_b}
        similarity={selectedRow.similarity}
        onBack={() => setSelectedRow(null)}
      />
    );
  }

  if (isLoading) return <div className="loading">Loading results...</div>;

  if (loadError) {
    return (
      <div>
        <div className="alert alert-error">{loadError}</div>
        <button className="btn btn-secondary" onClick={onBack}>Back</button>
      </div>
    );
  }

  const sortedRows = sortRows(resultRows, sortBy);
  const highCount = countRisk(resultRows, "HIGH");
  const mediumCount = countRisk(resultRows, "MEDIUM");
  const lowCount = countRisk(resultRows, "LOW");

  return (
    <div>
      <div className="page-header">
        <button className="btn btn-secondary btn-sm" onClick={onBack}>← Back to Dataset</button>
        <h1>Plagiarism Analysis Results</h1>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-label">Total Pairs</div>
          <div className="stat-value">{resultRows.length}</div>
        </div>
        <div className="stat-card danger">
          <div className="stat-label">High Risk</div>
          <div className="stat-value">{highCount}</div>
        </div>
        <div className="stat-card warning">
          <div className="stat-label">Medium Risk</div>
          <div className="stat-value">{mediumCount}</div>
        </div>
        <div className="stat-card success">
          <div className="stat-label">Low Risk</div>
          <div className="stat-value">{lowCount}</div>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.875rem" }}>
        <label className="form-label" style={{ margin: 0, whiteSpace: "nowrap" }}>Sort by:</label>
        <select
          className="form-select"
          style={{ width: "auto" }}
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value as "similarity" | "file_a")}
        >
          <option value="similarity">Similarity (High to Low)</option>
          <option value="file_a">File Name</option>
        </select>
      </div>

      {resultRows.length === 0 ? (
        <div className="empty-state">
          <h3>No pairs found</h3>
          <p>There were not enough files in the dataset to produce comparison pairs.</p>
        </div>
      ) : (
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Submission A</th>
                <th>Submission B</th>
                <th className="align-right">Similarity</th>
                <th className="align-center">Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {sortedRows.map((row) => (
                <tr
                  key={row.id}
                  className="clickable"
                  onClick={() => setSelectedRow(row)}
                  title="Click to view side-by-side comparison"
                >
                  <td className="mono">{row.file_a}</td>
                  <td className="mono">{row.file_b}</td>
                  <td className="align-right">
                    <div className="sim-bar-wrap">
                      <span style={{ fontWeight: 600, color: getRiskColor(row.risk), fontSize: "0.875rem" }}>
                        {(row.similarity * 100).toFixed(1)}%
                      </span>
                      <div className="sim-bar">
                        <div className="sim-bar-fill" style={{ width: `${row.similarity * 100}%`, background: getRiskColor(row.risk) }} />
                      </div>
                    </div>
                  </td>
                  <td className="align-center">
                    <span className={getRiskBadgeClass(row.risk)}>{row.risk}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
