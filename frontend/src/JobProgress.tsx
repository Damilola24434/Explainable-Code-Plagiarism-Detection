// about job progress component
// this is a react component that shows the progress of an analysis job
// it polls the backend for run status every 2 seconds
// it shows a progress bar, current stage, overall progress percentage  
// it shows elapsed analysis time
// when the job is complete it shows a button to view results
// if the job fails it shows an error message and a back button
// it uses the getRun API function to fetch run status from the backend
// this component is used after starting an analysis run to track its progress  
// and provide feedback to the user until the analysis is complete or fails.
// job progress is the UI component that manages and displays the analysis job status to the user.
import { useState, useEffect, useRef } from "react";
import { getRun, type Run } from "./api/runs";

interface Props {
  runId: string;
  onComplete: () => void;
  onCancel: () => void;
}

const stages = [
  { key: "INGEST", label: "Ingesting Files"        },
  { key: "TOKENS", label: "Tokenising Source Code" },
  { key: "AST",    label: "Parsing Syntax Trees"   },
  { key: "REPORT", label: "Generating Report"      },
];

type PollTimerRef = {
  current: ReturnType<typeof setInterval> | null;
};

type RunWarning = {
  stage?: string;
  path?: string;
  reason?: string;
};
// helper to stop polling timer
function stopTimer(timerRef: PollTimerRef) {
  // stop polling timer
  if (!timerRef.current) return;
  clearInterval(timerRef.current);
  timerRef.current = null;
}
// helper to get run title
function getRunTitle(run: Run): string {
  // title by run status
  if (run.status === "DONE") return "Analysis Complete";
  if (run.status === "FAILED") return "Analysis Failed";
  return "Analysis In Progress";
}
// helper to format duration
function formatDuration(totalSeconds: number): string {
  const safeSeconds = Math.max(0, Math.floor(totalSeconds));
  const hours = Math.floor(safeSeconds / 3600);
  const minutes = Math.floor((safeSeconds % 3600) / 60);
  const seconds = safeSeconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${seconds}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }
  return `${seconds}s`;
}
// helper to get analysis duration
function getAnalysisDuration(run: Run): string | null {
  if (!run.started_at) {
    return null;
  }

  const startedAt = new Date(run.started_at).getTime();
  const finishedAt = run.finished_at
    ? new Date(run.finished_at).getTime()
    : run.completed_at
      ? new Date(run.completed_at).getTime()
      : Date.now();

  if (Number.isNaN(startedAt) || Number.isNaN(finishedAt)) {
    return null;
  }

  return formatDuration((finishedAt - startedAt) / 1000);
}
// main component
export default function JobProgress({ runId, onComplete, onCancel }: Props) {
  const [runData, setRunData] = useState<Run | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadRunStatus = async () => {
    // get run status
    try {
      const nextRun = await getRun(runId);
      setRunData(nextRun);
      if (nextRun.status === "DONE" || nextRun.status === "FAILED") {
        stopTimer(timerRef);
      }
    } catch (error) {
      console.error("poll run status", error);
      setLoadError("Failed to retrieve run status.");
      stopTimer(timerRef);
    }
  };

  useEffect(() => {
    // start polling
    loadRunStatus();
    timerRef.current = setInterval(loadRunStatus, 2000);

    // cleanup polling
    return () => stopTimer(timerRef);
  }, [runId]);

  if (loadError) {
    return (
      <section className="flow-section progress-shell">
        <div>
          <div className="alert alert-error">{loadError}</div>
          <button className="btn btn-secondary" onClick={onCancel}>Back to Dataset</button>
        </div>
      </section>
    );
  }

  if (!runData) {
    return <div className="loading">Loading...</div>;
  }

  const currentStageIdx = stages.findIndex((stage) => stage.key === runData.stage);
  const isDone = runData.status === "DONE";
  const isFailed = runData.status === "FAILED";
  const fillClass = isDone ? "done" : isFailed ? "failed" : "";
  const analysisDuration = getAnalysisDuration(runData);
  const warnings = Array.isArray(runData.config_json?.warnings)
    ? (runData.config_json.warnings as RunWarning[])
    : [];

  return (
    <section className="flow-section progress-shell">
      <div className="progress-panel">
        <div className="progress-heading">
          <h2>{getRunTitle(runData)}</h2>
          <p className="run-meta">Run ID: {runId.slice(0, 8)}...</p>
        </div>

        <div className="progress-overview">
          <div className="progress-summary">
            <span className="text-small">Progress</span>
            <span className="text-small text-muted">{runData.progress_pct}%</span>
          </div>
          <div className="progress-bar">
            <div className={`progress-fill ${fillClass}`} style={{ width: `${runData.progress_pct}%` }} />
          </div>
          {analysisDuration && (
            <div className="text-small text-muted">
              {isDone || isFailed ? "Time" : "Elapsed"}: {analysisDuration}
            </div>
          )}
        </div>

        {runData.error_message && (
          <div className="alert alert-error">{runData.error_message}</div>
        )}
        {warnings.length > 0 && (
          <div className="alert alert-warning">
            <strong>Analysis warnings</strong>
            <ul className="compact-list">
              {warnings.slice(0, 8).map((warning, index) => (
                <li key={`${warning.path ?? "run"}-${warning.reason ?? index}`}>
                  {warning.stage ? `${warning.stage}: ` : ""}
                  {warning.path ? `${warning.path} - ` : ""}
                  {warning.reason ?? "Warning recorded"}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div>
          <p className="section-kicker">Stages</p>
          <ul className="stage-list">
            {stages.map((stage, i) => {
              const isCompleted = isDone || currentStageIdx > i;
              const isActive = runData.status === "RUNNING" && currentStageIdx === i;
              return (
                <li key={stage.key} className={`stage-item${isActive ? " active" : ""}`}>
                  <div className={`stage-number${isCompleted ? " completed" : isActive ? " active" : ""}`}>
                    {isCompleted ? "✓" : i + 1}
                  </div>
                  <span className={`stage-label${isActive ? " active" : isCompleted ? " completed" : ""}`}>
                    {stage.label}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="progress-actions">
          {isDone && !isFailed ? (
            <button className="btn btn-primary" onClick={onComplete}>View Results</button>
          ) : (
            <button className="btn btn-secondary" onClick={onCancel}>{isFailed ? "Back to Dataset" : "Cancel"}</button>
          )}
        </div>
      </div>
    </section>
  );
}
