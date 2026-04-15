# about tasks.py file:
# this file contains the background task logic for analysis jobs.
# When  runs.py starts a run, this  files does the heavey background job processing. it helps to loas files from DB
# run analysus pipeline stages ( ingest, token, ast, report)
# fr now the ast and token base a plceholder is kept
# it save progress and final results back to the databse.
# runs is like the manager of the background analysis jobs
# tasks.py is the worker that actually perform the analysis


import time
import os
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.celery import celery_app
from app.core.db import SessionLocal
from app.models.models import CandidatePair, File, FileFingerprint, MatchEvidence, PairResult, Run, Submission
from app.pipeline.ast.run_stage import compare_prepared_files, prepare_ast_file
from app.pipeline.token.run_stage import compare_prepared_token_files, prepare_token_file, serialize_fingerprints
from similarity.thresholds import K_GRAM_SIZE


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


def get_pair_result_map(db: Session, run_id: str) -> dict[tuple[str, str], PairResult]:
    rows = db.query(PairResult).filter(PairResult.run_id == run_id).all()
    return {(str(row.file_a_id), str(row.file_b_id)): row for row in rows}


def get_candidate_pair_keys(db: Session, run_id: str) -> set[tuple[str, str]]:
    rows = db.query(CandidatePair).filter(CandidatePair.run_id == run_id).all()
    return {(str(row.file_a_id), str(row.file_b_id)) for row in rows}


def blended_final_score(fingerprint_score: float, ast_score: float) -> float:
    if ast_score > 0:
        return round(ast_score, 6)
    return round(fingerprint_score, 6)


def run_token_stage(db: Session, run_id: str) -> None:
    update_run(db, run_id, stage="TOKENS", progress_pct=30)
    files = get_run_files(db, run_id)
    prepared_files = []
    fingerprint_rows: list[FileFingerprint] = []

    for file_row in files:
        prepared = prepare_token_file(
            file_id=file_row.id,
            path=file_row.path,
            content=file_row.content,
            language=file_row.language,
            k=K_GRAM_SIZE,
        )
        if prepared is None:
            continue

        prepared_files.append(prepared)
        fingerprint_rows.append(
            FileFingerprint(
                run_id=run_id,
                file_id=file_row.id,
                k=K_GRAM_SIZE,
                w=K_GRAM_SIZE,
                algo_version="token-jaccard-v1",
                fingerprint_blob=serialize_fingerprints(prepared.fingerprints),
                fingerprint_count=len(prepared.fingerprints),
            )
        )

    if fingerprint_rows:
        db.add_all(fingerprint_rows)
        db.commit()

    update_run(db, run_id, stage="TOKENS", progress_pct=50)
    comparisons = compare_prepared_token_files(prepared_files, k=K_GRAM_SIZE)
    pair_map = get_pair_result_map(db, run_id)
    candidate_rows: list[CandidatePair] = []
    evidence_rows: list[MatchEvidence] = []

    for comparison in comparisons:
        file_a_id = comparison["file_a_id"]
        file_b_id = comparison["file_b_id"]
        pair_key = (str(file_a_id), str(file_b_id))
        score = round(comparison["fingerprint_score"], 6)

        candidate_rows.append(
            CandidatePair(
                run_id=run_id,
                file_a_id=file_a_id,
                file_b_id=file_b_id,
                overlap_count=comparison["overlap_count"],
                fingerprint_score=score,
            )
        )

        existing = pair_map.get(pair_key)
        if existing is None:
            existing = PairResult(
                run_id=run_id,
                file_a_id=file_a_id,
                file_b_id=file_b_id,
                final_score=blended_final_score(score, 0.0),
                fingerprint_score=score,
                ast_score=0.0,
            )
            db.add(existing)
            pair_map[pair_key] = existing
        else:
            existing.fingerprint_score = score
            existing.final_score = blended_final_score(score, existing.ast_score)

        for evidence in comparison["evidence"]:
            for loc_a, loc_b in zip(evidence["locations_a"], evidence["locations_b"]):
                evidence_rows.append(
                    MatchEvidence(
                        run_id=run_id,
                        file_a_id=file_a_id,
                        file_b_id=file_b_id,
                        a_start=loc_a,
                        a_end=loc_a + K_GRAM_SIZE,
                        b_start=loc_b,
                        b_end=loc_b + K_GRAM_SIZE,
                        kind="TOKEN",
                        weight=float(evidence["support_count"]),
                    )
                )

    if candidate_rows:
        db.add_all(candidate_rows)
    if evidence_rows:
        db.add_all(evidence_rows)
    if candidate_rows or evidence_rows or comparisons:
        db.commit()

    analysis_stage_delay()


def run_ast_stage(db: Session, run_id: str) -> None:
    update_run(db, run_id, stage="AST", progress_pct=55)

    files = get_run_files(db, run_id)
    prepared_files = []
    for file_row in files:
        prepared = prepare_ast_file(
            file_id=str(file_row.id),
            path=file_row.path,
            content=file_row.content,
            language=file_row.language,
        )
        if prepared is not None:
            prepared_files.append(prepared)

    candidate_pair_keys = get_candidate_pair_keys(db, run_id)
    comparisons = compare_prepared_files(
        prepared_files,
        n=3,
        candidate_pairs=candidate_pair_keys if candidate_pair_keys else None,
    )
    pair_map = get_pair_result_map(db, run_id)
    evidence_rows: list[MatchEvidence] = []
    for comparison in comparisons:
        pair_key = (str(comparison["file_a_id"]), str(comparison["file_b_id"]))
        ast_score = round(comparison["ast_score"], 6)
        existing = pair_map.get(pair_key)
        if existing is None:
            existing = PairResult(
                run_id=run_id,
                file_a_id=comparison["file_a_id"],
                file_b_id=comparison["file_b_id"],
                fingerprint_score=0.0,
                ast_score=0.0,
            )
            db.add(existing)
            pair_map[pair_key] = existing

        existing.ast_score = ast_score
        existing.final_score = blended_final_score(existing.fingerprint_score, ast_score)

        for evidence in comparison["evidence"]:
            for loc_a, loc_b in zip(evidence["locations_a"], evidence["locations_b"]):
                evidence_rows.append(
                    MatchEvidence(
                        run_id=run_id,
                        file_a_id=comparison["file_a_id"],
                        file_b_id=comparison["file_b_id"],
                        a_start=loc_a["start_byte"],
                        a_end=loc_a["end_byte"],
                        b_start=loc_b["start_byte"],
                        b_end=loc_b["end_byte"],
                        kind="AST",
                        weight=float(evidence["support_count"]),
                    )
                )

    if evidence_rows:
        db.add_all(evidence_rows)
    if evidence_rows or comparisons:
        db.commit()

    update_run(db, run_id, stage="AST", progress_pct=75)
    analysis_stage_delay()


def get_existing_pairs(db: Session, run_id: str) -> set[tuple[str, str]]:
    # load pair keys
    pairs = db.query(PairResult).filter(PairResult.run_id == run_id).all()
    return {(str(pair.file_a_id), str(pair.file_b_id)) for pair in pairs}

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
    TOKENS is still a placeholder. AST now runs real parsing/comparison.
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
        update_run(db, run_id, stage="INGEST", progress_pct=10)
        update_run(db, run_id, stage="INGEST", progress_pct=25)

        # run placeholder stages
        run_token_stage(db, run_id)
        run_ast_stage(db, run_id)

        # build report
        update_run(db, run_id, stage="REPORT", progress_pct=80)
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
