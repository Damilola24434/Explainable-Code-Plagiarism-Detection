// this component shws two code sde by side so user the professor can visually comaptre suspicious plagiarism pairs
// it also receives a similarity score and convers it into a risk level to show a colored badge at the top
// it has a button to return to results page
// a title and similarity /risk badge
// a loading message while fetching.
// an error message if file loading fails.
// two code panels side by side once data loads successfully.
// this is a maual review page where professor can inspaecr files sisde by side that have high similarity score 
// and decide if the similarity looks like it was copied rom a sourece

import { useState, useEffect, type ReactNode } from "react";
import { getPairEvidence, type MatchEvidence } from "./api/runs";

const API_BASE = "/api";
const MIN_HIGHLIGHT_SIMILARITY = 0.2;
const MAX_HIGHLIGHT_EVIDENCE_ROWS = 6;
const FULL_HIGHLIGHT_SIMILARITY = 0.95;

interface Props {
  runId: string;
  pairId: string;
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

function byteOffsetToStringIndex(text: string, byteOffset: number): number {
  if (byteOffset <= 0) return 0;

  let bytesSeen = 0;
  for (let i = 0; i < text.length; i += 1) {
    const codePoint = text.codePointAt(i);
    if (codePoint === undefined) break;
    const char = String.fromCodePoint(codePoint);
    const charBytes = new TextEncoder().encode(char).length;
    if (bytesSeen >= byteOffset) return i;
    bytesSeen += charBytes;
    if (bytesSeen >= byteOffset) return i + char.length;
    if (char.length === 2) i += 1;
  }

  return text.length;
}

function normalizeRanges(ranges: Array<{ start: number; end: number }>) {
  const filtered = ranges
    .filter((range) => range.end > range.start)
    .sort((a, b) => a.start - b.start);

  if (filtered.length === 0) return [];

  const merged = [filtered[0]];
  for (let i = 1; i < filtered.length; i += 1) {
    const current = filtered[i];
    const last = merged[merged.length - 1];
    if (current.start <= last.end) {
      last.end = Math.max(last.end, current.end);
    } else {
      merged.push({ ...current });
    }
  }
  return merged;
}

function renderHighlightedCode(text: string, ranges: Array<{ start: number; end: number }>) {
  const merged = normalizeRanges(ranges);
  if (merged.length === 0) return text;

  const parts: ReactNode[] = [];
  let cursor = 0;

  merged.forEach((range, index) => {
    if (cursor < range.start) {
      parts.push(<span key={`plain-${index}-${cursor}`}>{text.slice(cursor, range.start)}</span>);
    }
    parts.push(
      <mark key={`mark-${index}-${range.start}`} className="code-highlight">
        {text.slice(range.start, range.end)}
      </mark>
    );
    cursor = range.end;
  });

  if (cursor < text.length) {
    parts.push(<span key={`tail-${cursor}`}>{text.slice(cursor)}</span>);
  }

  return parts;
}

function selectVisibleEvidenceRows(evidence: MatchEvidence[], similarity: number): MatchEvidence[] {
  if (similarity < MIN_HIGHLIGHT_SIMILARITY) {
    return [];
  }
  if (similarity >= FULL_HIGHLIGHT_SIMILARITY) {
    return evidence;
  }
  return evidence.slice(0, MAX_HIGHLIGHT_EVIDENCE_ROWS);
}

export default function SideBySideComparison({
  runId,
  pairId,
  fileAId,
  fileBId,
  fileAName,
  fileBName,
  similarity,
  datasetName,
  onBack,
}: Props) {
  const [leftText, setLeftText] = useState<string | null>(null);
  const [rightText, setRightText] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<MatchEvidence[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);

  void datasetName;

  const loadFiles = async () => {
    // fetch both files
    try {
      const [left, right, evidenceRows] = await Promise.all([
        fetchFileText(fileAId),
        fetchFileText(fileBId),
        getPairEvidence(runId, pairId),
      ]);
      setLeftText(left);
      setRightText(right);
      setEvidence(evidenceRows);
    } catch (error) {
      console.error("load file content", error);
      setLoadError("Failed to load file content.");
    }
  };

  useEffect(() => {
    // load when ids change
    loadFiles();
  }, [fileAId, fileBId, runId, pairId]);

  const risk = getRiskLabel(similarity);
  const badgeClass = getRiskBadge(risk);
  const visibleEvidence = selectVisibleEvidenceRows(evidence, similarity);
  const leftRanges =
    leftText === null
      ? []
      : visibleEvidence.map((row) => ({
          start: byteOffsetToStringIndex(leftText, row.a_start),
          end: byteOffsetToStringIndex(leftText, row.a_end),
        }));
  const rightRanges =
    rightText === null
      ? []
      : visibleEvidence.map((row) => ({
          start: byteOffsetToStringIndex(rightText, row.b_start),
          end: byteOffsetToStringIndex(rightText, row.b_end),
        }));

  return (
    <section className="screen page-compare">
      <div className="page-header compare-header">
        <div className="compare-heading">
          <div>
            <p className="section-kicker">Manual Review</p>
            <h2>File Comparison</h2>
            <p className="page-subtitle">
              {similarity >= FULL_HIGHLIGHT_SIMILARITY
                ? "Files are near-identical, so all AST evidence spans are highlighted."
                : similarity >= MIN_HIGHLIGHT_SIMILARITY
                  ? "Compare the strongest AST-matched regions side by side."
                  : "Similarity is low, so structural highlights are hidden to avoid boilerplate noise."}
            </p>
          </div>
        </div>
        <span className={badgeClass}>
          {risk} - {(similarity * 100).toFixed(1)}% similar
        </span>
      </div>
      <button type="button" className="secondary-button" onClick={onBack}>
        Back to Results
      </button>

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
            <pre>{renderHighlightedCode(leftText, leftRanges)}</pre>
          </div>
          <div className="code-pane">
            <div className="code-pane-header">{fileBName}</div>
            <pre>{renderHighlightedCode(rightText, rightRanges)}</pre>
          </div>
        </div>
      )}
    </section>
  );
}
