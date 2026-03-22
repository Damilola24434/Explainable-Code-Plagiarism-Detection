import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000/api";

interface Props {
  fileAId: string;
  fileBId: string;
  fileAName: string;
  fileBName: string;
  similarity: number;
  onBack: () => void;
}

function getRiskLabel(score: number): "HIGH" | "MEDIUM" | "LOW" {
  // map score to risk
  if (score >= 0.7) return "HIGH";
  if (score >= 0.4) return "MEDIUM";
  return "LOW";
}

function getRiskBadge(risk: "HIGH" | "MEDIUM" | "LOW"): string {
  // map risk to style
  if (risk === "HIGH") return "badge badge-high";
  if (risk === "MEDIUM") return "badge badge-medium";
  return "badge badge-low";
}

async function fetchFileText(fileId: string): Promise<string> {
  // load one file content
  const response = await fetch(`${API_BASE}/files/${fileId}`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.text();
}

export default function SideBySideComparison({
  fileAId,
  fileBId,
  fileAName,
  fileBName,
  similarity,
  onBack,
}: Props) {
  const [leftText, setLeftText] = useState<string | null>(null);
  const [rightText, setRightText] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadFiles = async () => {
    // fetch both files
    try {
      const [left, right] = await Promise.all([fetchFileText(fileAId), fetchFileText(fileBId)]);
      setLeftText(left);
      setRightText(right);
    } catch (error) {
      console.error("load file content", error);
      setLoadError("Failed to load file content.");
    }
  };

  useEffect(() => {
    // load when ids change
    loadFiles();
  }, [fileAId, fileBId]);

  const risk = getRiskLabel(similarity);
  const badgeClass = getRiskBadge(risk);

  return (
    <div>
      <div className="page-header">
        <button className="btn btn-secondary btn-sm" onClick={onBack}>← Back to Results</button>
        <h1>File Comparison</h1>
        <span className={badgeClass} style={{ fontSize: "0.8125rem", padding: "0.25rem 0.75rem" }}>
          {risk} - {(similarity * 100).toFixed(1)}% similar
        </span>
      </div>

      {loadError ? (
        <div className="alert alert-error">{loadError}</div>
      ) : leftText === null || rightText === null ? (
        <div className="loading">Loading file content...</div>
      ) : (
        <div className="code-grid">
          <div className="code-pane">
            <div className="code-pane-header">{fileAName}</div>
            <pre>{leftText}</pre>
          </div>
          <div className="code-pane">
            <div className="code-pane-header">{fileBName}</div>
            <pre>{rightText}</pre>
          </div>
        </div>
      )}
    </div>
  );
}
