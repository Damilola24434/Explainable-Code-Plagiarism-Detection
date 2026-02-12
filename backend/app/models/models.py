import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey,
    DateTime, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA
from sqlalchemy.sql import func
from app.core.db import Base


# 1) collections
class Collection(Base):
    __tablename__ = "collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), nullable=False)  # FK to users later
    name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_collections_owner_name"),
    )


# 2) datasets
class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("collection_id", "name", name="uq_datasets_collection_name"),
        Index("ix_datasets_collection_id", "collection_id"),
    )


# 3) submissions
class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    student_label = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("dataset_id", "student_label", name="uq_submissions_dataset_student"),
        Index("ix_submissions_dataset_id", "dataset_id"),
    )


# 4) files
class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    path = Column(Text, nullable=False)
    language = Column(Text, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    content_hash = Column(Text, nullable=False)
    storage_key = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("submission_id", "path", name="uq_files_submission_path"),
        Index("ix_files_submission_id", "submission_id"),
        Index("ix_files_content_hash", "content_hash"),
    )


# 5) runs
class Run(Base):
    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    status = Column(Text, nullable=False)  # QUEUED, PROCESSING, FAILED, DONE
    stage = Column(Text, nullable=False)   # INGEST, TOKENS, FINGERPRINT, AST, AGGREGATE, REPORT
    progress_pct = Column(Integer, nullable=False, default=0)
    config_json = Column(JSONB, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_runs_dataset_created_at", "dataset_id", "created_at"),
        Index("ix_runs_dataset_id", "dataset_id"),
    )


# 6) file_fingerprints
class FileFingerprint(Base):
    __tablename__ = "file_fingerprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    k = Column(Integer, nullable=False)
    w = Column(Integer, nullable=False)
    algo_version = Column(Text, nullable=False)
    fingerprint_blob = Column(BYTEA, nullable=False)  # store compressed bytes
    fingerprint_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("run_id", "file_id", name="uq_file_fingerprints_run_file"),
        Index("ix_file_fingerprints_file_id", "file_id"),
        Index("ix_file_fingerprints_run_id", "run_id"),
    )


# 7) candidate_pairs
class CandidatePair(Base):
    __tablename__ = "candidate_pairs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    file_a_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    file_b_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    overlap_count = Column(Integer, nullable=False)
    fingerprint_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("run_id", "file_a_id", "file_b_id", name="uq_candidate_pairs_run_a_b"),
        Index("ix_candidate_pairs_run_id", "run_id"),
        Index("ix_candidate_pairs_run_score", "run_id", "fingerprint_score"),
    )


# 8) pair_results
class PairResult(Base):
    __tablename__ = "pair_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    file_a_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    file_b_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    final_score = Column(Float, nullable=False)
    fingerprint_score = Column(Float, nullable=False)
    ast_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("run_id", "file_a_id", "file_b_id", name="uq_pair_results_run_a_b"),
        Index("ix_pair_results_run_id", "run_id"),
        Index("ix_pair_results_run_final_score", "run_id", "final_score"),
    )


# 9) match_evidence
class MatchEvidence(Base):
    __tablename__ = "match_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    file_a_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    file_b_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)
    a_start = Column(Integer, nullable=False)
    a_end = Column(Integer, nullable=False)
    b_start = Column(Integer, nullable=False)
    b_end = Column(Integer, nullable=False)
    kind = Column(Text, nullable=False)  # TOKEN, AST
    weight = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_match_evidence_run_a_b", "run_id", "file_a_id", "file_b_id"),
    )


# 10) run_reports
class RunReport(Base):
    __tablename__ = "run_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    csv_storage_key = Column(Text, nullable=True)
    pdf_storage_key = Column(Text, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("run_id", name="uq_run_reports_run_id"),
        Index("ix_run_reports_run_id", "run_id"),
    )
