// this component shws two code sde by side so user the professor can visually comaptre suspicious plagiarism pairs
// it also receives a similarity score and convers it into a risk level to show a colored badge at the top
// it has a button to return to results page
// a title and similarity /risk badge
// a loading message while fetching.
// an error message if file loading fails.
// two code panels side by side once data loads successfully.
// this is a maual review page where professor can inspaecr files sisde by side that have high similarity score 
// and decide if the similarity looks like it was copied rom a sourece

import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000/api";

interface Props {
  fileAId: string;
  fileBId: string;
  fileAName: string;
  fileBName: string;
  similarity: number;
  datasetName?: string;
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
  datasetName: _datasetName,
  onBack: _onBack,
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
    <section className="screen page-compare">
      <div className="page-header compare-header">
        <div className="compare-heading">
          <div>
            <p className="section-kicker">Manual Review</p>
            <h2>File Comparison</h2>
            <p className="page-subtitle">
              Compare the flagged files side by side.
            </p>
          </div>
        </div>
        <span className={badgeClass}>
          {risk} - {(similarity * 100).toFixed(1)}% similar
        </span>
      </div>

      {loadError ? (
        <div className="flow-section">
          <div className="alert alert-error">{loadError}</div>
        </div>
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
    </section>
  );
}
