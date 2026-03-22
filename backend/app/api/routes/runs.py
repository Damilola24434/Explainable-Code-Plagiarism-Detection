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




import os
import threading
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.models import File, PairResult, Run
from app.schemas.runs import RunCreate, RunOut, SimilarityResultOut
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
