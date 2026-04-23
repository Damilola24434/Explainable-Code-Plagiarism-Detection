# About runs.py file:
# This file  handles plagrism analysis jobs("runs").
# This file manages  the anayis process and not the analusis logic itself.
# how it works:
# user cicks run analyis in the fronend
#runs.y receive that request.
# It then creates a run job in the databsde.
# It lets the frontend check> is the run still working? is it finished? what are the results?
# it is basically like a manager for plagrism check. it start and tracks job statis.
# it does nt do the AST parsi itself, it does not do the tokenization itself, it does not do the similarity checking itself.
# those are done in the tasks/pipeline.py file.




import io
import os
import threading
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import File, MatchEvidence, PairResult, Run
from app.schemas.runs import MatchEvidenceOut, RunCreate, RunOut, SimilarityResultOut
from app.tasks import run_pipeline

router = APIRouter(prefix="/api/runs", tags=["runs"])


def start_run_job(run_id: str) -> None:
    # In container/prod, queue with Celery + Redis.
    # For local dev fallback, run directly in a background thread.
    if os.getenv("USE_REDIS", "0") == "1":
        try:
            run_pipeline.delay(run_id)
            return
        except Exception:
            pass

    threading.Thread(
        target=run_pipeline.run,
        args=(run_id,),
        daemon=True,
    ).start()


def get_risk_label(score: float) -> str:
    # map score to risk level
    if score >= 0.7:
        return "HIGH"
    if score >= 0.4:
        return "MEDIUM"
    return "LOW"


def get_file_path_map(db: Session, pairs: List[PairResult]) -> dict[str, str]:
    # collect ids
    file_ids = {str(pair.file_a_id) for pair in pairs} | {str(pair.file_b_id) for pair in pairs}
    if not file_ids:
        return {}

    # map id -> path
    files = db.query(File).filter(File.id.in_(file_ids)).all()
    return {str(file.id): file.path for file in files}


def build_result_rows(pairs: List[PairResult], file_map: dict[str, str]) -> List[SimilarityResultOut]:
    # build api rows
    rows: List[SimilarityResultOut] = []
    for pair in pairs:
        score = pair.final_score
        rows.append(
            SimilarityResultOut(
                id=pair.id,
                file_a=file_map.get(str(pair.file_a_id), str(pair.file_a_id)),
                file_b=file_map.get(str(pair.file_b_id), str(pair.file_b_id)),
                file_a_id=pair.file_a_id,
                file_b_id=pair.file_b_id,
                similarity=round(score, 3),
                risk=get_risk_label(score),
            )
        )

    # show high scores first
    rows.sort(key=lambda row: row.similarity, reverse=True)
    return rows


@router.post("/", response_model=RunOut, status_code=status.HTTP_201_CREATED)
def create_run(payload: RunCreate, db: Session = Depends(get_db)):
    """Create a Run record and enqueue a background job."""
    run = Run(
        dataset_id=payload.dataset_id,
        status="QUEUED",
        stage="INGEST",
        progress_pct=0,
        config_json=payload.config_json or {},
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        # start analysis job
        start_run_job(str(run.id))
    except Exception as exc:
        # save startup error
        run.status = "FAILED"
        run.error_message = f"Failed to start pipeline: {exc}"
        db.commit()

    return run


@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: UUID, db: Session = Depends(get_db)):
    """Return job status for a run."""
    # get run status
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/dataset/{dataset_id}/history", response_model=List[RunOut])
def get_dataset_run_history(dataset_id: UUID, db: Session = Depends(get_db)):
    """Return all runs for a dataset, sorted by created_at descending."""
    runs = (
        db.query(Run)
        .filter(Run.dataset_id == dataset_id)
        .order_by(Run.created_at.desc())
        .all()
    )
    return runs


@router.get("/{run_id}/results", response_model=List[SimilarityResultOut])
def get_run_results(run_id: UUID, db: Session = Depends(get_db)):
    """
    Return similarity results for a completed run.
    Each row represents one file pair with a similarity score and risk label.
    """
    # check run
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status not in ("DONE", "FAILED"):
        raise HTTPException(status_code=409, detail="Run is not finished yet")

    # get pair rows
    pairs = db.query(PairResult).filter(PairResult.run_id == run_id).all()

    # map ids to file paths
    file_map = get_file_path_map(db, pairs)

    # return api response
    return build_result_rows(pairs, file_map)


@router.get("/{run_id}/results/{pair_id}/evidence", response_model=List[MatchEvidenceOut])
def get_pair_evidence(run_id: UUID, pair_id: UUID, db: Session = Depends(get_db)):
    """Return saved evidence rows for one result pair."""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    pair = db.query(PairResult).filter(PairResult.id == pair_id, PairResult.run_id == run_id).first()
    if not pair:
        raise HTTPException(status_code=404, detail="Pair result not found")

    evidence_rows = (
        db.query(MatchEvidence)
        .filter(
            MatchEvidence.run_id == run_id,
            MatchEvidence.file_a_id == pair.file_a_id,
            MatchEvidence.file_b_id == pair.file_b_id,
            MatchEvidence.kind == "AST",
        )
        .order_by(MatchEvidence.kind.asc(), MatchEvidence.weight.desc(), MatchEvidence.created_at.asc())
        .all()
    )
    return evidence_rows


@router.get("/{run_id}/export-pdf")
def export_run_report_pdf(run_id: UUID, db: Session = Depends(get_db)):
    """Return a PDF summary report for a completed run."""
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status not in ("DONE", "FAILED"):
        raise HTTPException(status_code=409, detail="Run is not finished yet")

    pairs = db.query(PairResult).filter(PairResult.run_id == run_id).all()
    file_map = get_file_path_map(db, pairs)

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 50
    y = height - margin

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, y, "Plagiarism Detection Report")
    y -= 30

    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, y, f"Run ID: {run.id}")
    pdf.drawString(width / 2, y, f"Dataset ID: {run.dataset_id}")
    y -= 16
    pdf.drawString(margin, y, f"Status: {run.status}")
    pdf.drawString(width / 2, y, f"Stage: {run.stage}")
    y -= 16
    pdf.drawString(margin, y, f"Created At: {run.created_at}")
    y -= 30

    total_pairs = len(pairs)
    high_count = sum(1 for pair in pairs if pair.final_score >= 0.7)
    medium_count = sum(1 for pair in pairs if 0.4 <= pair.final_score < 0.7)
    low_count = total_pairs - high_count - medium_count

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, f"Total pairs: {total_pairs}")
    y -= 18
    pdf.setFont("Helvetica", 11)
    pdf.drawString(margin, y, f"High risk: {high_count}")
    pdf.drawString(width / 2, y, f"Medium risk: {medium_count}")
    pdf.drawString(width - 150, y, f"Low risk: {low_count}")
    y -= 30

    if total_pairs == 0:
        pdf.drawString(margin, y, "No similarity pairs were generated for this run.")
    else:
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margin, y, "File A")
        pdf.drawString(margin + 200, y, "File B")
        pdf.drawString(margin + 400, y, "Similarity")
        pdf.drawString(margin + 500, y, "Risk")
        y -= 18
        pdf.setLineWidth(0.5)
        pdf.line(margin, y, width - margin, y)
        y -= 14

        pdf.setFont("Helvetica", 10)
        for pair in pairs:
            if y < margin + 40:
                pdf.showPage()
                y = height - margin
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(margin, y, "File A")
                pdf.drawString(margin + 200, y, "File B")
                pdf.drawString(margin + 400, y, "Similarity")
                pdf.drawString(margin + 500, y, "Risk")
                y -= 18
                pdf.line(margin, y, width - margin, y)
                y -= 14
                pdf.setFont("Helvetica", 10)

            similarity_pct = f"{pair.final_score * 100:.1f}%"
            risk_label = get_risk_label(pair.final_score)
            pdf.drawString(margin, y, file_map.get(str(pair.file_a_id), str(pair.file_a_id)))
            pdf.drawString(margin + 200, y, file_map.get(str(pair.file_b_id), str(pair.file_b_id)))
            pdf.drawString(margin + 400, y, similarity_pct)
            pdf.drawString(margin + 500, y, risk_label)
            y -= 16

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    filename = f"plagiarism-report-{run.id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
