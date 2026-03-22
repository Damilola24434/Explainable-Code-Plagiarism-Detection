# about tasks.py file:
# this file contains the background task logic for analysis jobs.
# When  runs.py starts a run, this  files does the heavey background job processing. it helps to loas files from DB
# run analysus pipeline stages ( ingest, token, ast, report)
# fr now the ast and token base a plceholder is kept
# it save progress and final results back to the databse.
# runs is like the manager of the background analysis jobs
# tasks.py is the worker that actually perform the analysis


# Bottom line: The system structure is in place, but the actual similarity analysis (token + AST) hasn't been implemented yet.
import random
import time
import os
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.celery import celery_app
from app.core.db import SessionLocal
from app.models.models import File, PairResult, Run, Submission


ANALYSIS_STAGE_DELAY_SECONDS = float(os.getenv("ANALYSIS_STAGE_DELAY_SECONDS", "1"))


def analysis_stage_delay() -> None:
    # optional delay for placeholder analysis stages (TOKENS/AST)
    if ANALYSIS_STAGE_DELAY_SECONDS > 0:
        time.sleep(ANALYSIS_STAGE_DELAY_SECONDS)


def open_db() -> Session:
    return SessionLocal()


def update_run(
    db: Session,
    run_id: str,
    status: Optional[str] = None,
    stage: Optional[str] = None,
    progress_pct: Optional[int] = None,
    error_message: Optional[str] = None,
    started_at: Optional[datetime] = None,
    finished_at: Optional[datetime] = None,
) -> None:
    # get run
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        return

    # set fields
    if status is not None:
        run.status = status
    if stage is not None:
        run.stage = stage
    if progress_pct is not None:
        run.progress_pct = progress_pct
    if error_message is not None:
        run.error_message = error_message
    if started_at is not None:
        run.started_at = started_at
    if finished_at is not None:
        run.finished_at = finished_at

    # save changes
    db.commit()


def get_run_files(db: Session, run_id: str) -> list[File]:
    # find run
    run = db.query(Run).filter(Run.id == run_id).first()
    if not run:
        return []

    # get files in this run dataset
    return (
        db.query(File)
        .join(Submission, Submission.id == File.submission_id)
        .filter(Submission.dataset_id == run.dataset_id)
        .all()
    )

#The overall pipeline is implemented and working (run tracking, stages, database writes).
#However, the core analysis logic is still incomplete.
#The token analysis stage is currently just a placeholder.
#The AST (Abstract Syntax Tree) analysis stage is also a placeholder.
#The final scoring is not meaningful yet—it uses random placeholder values.

def run_token_stage(db: Session, run_id: str) -> None:
    # placeholder token stage
    update_run(db, run_id, stage="TOKENS", progress_pct=30)
    analysis_stage_delay()
    update_run(db, run_id, stage="TOKENS", progress_pct=50)
    analysis_stage_delay()


def run_ast_stage(db: Session, run_id: str) -> None:
    # placeholder ast stage
    update_run(db, run_id, stage="AST", progress_pct=55)
    analysis_stage_delay()
    update_run(db, run_id, stage="AST", progress_pct=75)
    analysis_stage_delay()


def get_existing_pairs(db: Session, run_id: str) -> set[tuple[str, str]]:
    # load pair keys
    pairs = db.query(PairResult).filter(PairResult.run_id == run_id).all()
    return {(str(pair.file_a_id), str(pair.file_b_id)) for pair in pairs}

#The overall pipeline is implemented and working (run tracking, stages, database writes).
#However, the core analysis logic is still incomplete.
#The token analysis stage is currently just a placeholder.
#The AST (Abstract Syntax Tree) analysis stage is also a placeholder.
#The final scoring is not meaningful yet—it uses random placeholder values.

def build_placeholder_results(
    run_id: str,
    files: list[File],
    existing_pairs: set[tuple[str, str]],
) -> list[PairResult]:
    # build one row per file pair
    rows: list[PairResult] = []
    for index, file_a in enumerate(files):
        for file_b in files[index + 1 :]:
            pair_key = (str(file_a.id), str(file_b.id))
            if pair_key in existing_pairs:
                continue

            # placeholder score
            score = round(random.uniform(0.05, 0.99), 3)
            rows.append(
                PairResult(
                    run_id=run_id,
                    file_a_id=file_a.id,
                    file_b_id=file_b.id,
                    final_score=score,
                    fingerprint_score=score,
                    ast_score=score,
                )
            )
    return rows


def save_results(db: Session, rows: list[PairResult]) -> None:
    # save new rows
    if not rows:
        return
    db.add_all(rows)
    db.commit()


@celery_app.task(name="run_pipeline")
def run_pipeline(run_id: str) -> None:
    """
    Run stages: INGEST -> TOKENS -> AST -> REPORT.
    TOKENS and AST are placeholders for now.
    """
    db = open_db()

    try:
        # start run
        update_run(
            db,
            run_id,
            status="RUNNING",
            stage="INGEST",
            progress_pct=0,
            started_at=datetime.utcnow(),
        )

        # ingest files
        files = get_run_files(db, run_id)
        update_run(db, run_id, stage="INGEST", progress_pct=10)
        update_run(db, run_id, stage="INGEST", progress_pct=25)

        # run placeholder stages
        run_token_stage(db, run_id)
        run_ast_stage(db, run_id)

        # build report
        update_run(db, run_id, stage="REPORT", progress_pct=80)
        existing_pairs = get_existing_pairs(db, run_id)
        rows = build_placeholder_results(run_id, files, existing_pairs)
        save_results(db, rows)
        update_run(db, run_id, stage="REPORT", progress_pct=95)

        # finish run
        update_run(
            db,
            run_id,
            status="DONE",
            stage="REPORT",
            progress_pct=100,
            finished_at=datetime.utcnow(),
        )
    except Exception as exc:
        # mark run failed
        update_run(
            db,
            run_id,
            status="FAILED",
            error_message=str(exc),
            finished_at=datetime.utcnow(),
        )
        raise
    finally:
        db.close()

