import uuid  # Used to generate unique identifiers for primary keys

from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey,
    DateTime, UniqueConstraint, Index
)  # Core SQLAlchemy column types and constraints

from sqlalchemy.dialects.postgresql import UUID, JSONB, BYTEA  # PostgreSQL-specific types
from sqlalchemy.sql import func  # Used for database functions like current timestamp

from app.core.db import Base  # Base class that all models inherit from


# =========================
# 1) collections
# =========================
# Represents a logical grouping of datasets owned by a user
class Collection(Base):
    __tablename__ = "collections"

    # Primary key using UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Will later reference a users table once authentication is implemented
    owner_id = Column(UUID(as_uuid=True), nullable=False)

    # Name of the collection
    name = Column(Text, nullable=False)

    # Timestamp automatically set when record is created
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Prevent same user from creating two collections with the same name
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_collections_owner_name"),
    )


# =========================
# 2) datasets
# =========================
# Each dataset belongs to a collection
class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key linking dataset to its parent collection
    # ondelete="CASCADE" ensures datasets are deleted if collection is deleted
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id", ondelete="CASCADE"), nullable=False)

    name = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Prevent duplicate dataset names inside the same collection
    # Add index for faster lookup by collection
    __table_args__ = (
        UniqueConstraint("collection_id", "name", name="uq_datasets_collection_name"),
        Index("ix_datasets_collection_id", "collection_id"),
    )


# =========================
# 3) submissions
# =========================
# Each submission represents a student's submission inside a dataset
class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Links submission to dataset
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)

    # Label identifying the student
    student_label = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Ensure one student label per dataset
    # Index helps with filtering by dataset
    __table_args__ = (
        UniqueConstraint("dataset_id", "student_label", name="uq_submissions_dataset_student"),
        Index("ix_submissions_dataset_id", "dataset_id"),
    )


# =========================
# 4) files
# =========================
# Represents individual source code files inside a submission
class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Links file to its submission
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)

    # File path inside submission
    path = Column(Text, nullable=False)

    # Programming language of the file
    language = Column(Text, nullable=False)

    # File size for reference
    size_bytes = Column(Integer, nullable=False)

    # Hash of file contents (used to detect duplicates quickly)
    content_hash = Column(Text, nullable=False)

    # Storage key for retrieving actual file content
    storage_key = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Prevent duplicate file paths in same submission
    # Indexes improve lookup speed
    __table_args__ = (
        UniqueConstraint("submission_id", "path", name="uq_files_submission_path"),
        Index("ix_files_submission_id", "submission_id"),
        Index("ix_files_content_hash", "content_hash"),
    )


# =========================
# 5) runs
# =========================
# Represents one execution of the plagiarism detection pipeline
class Run(Base):
    __tablename__ = "runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Run is always associated with a dataset
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)

    # Overall run status (QUEUED, PROCESSING, FAILED, DONE)
    status = Column(Text, nullable=False)

    # Current processing stage (INGEST, TOKENS, etc.)
    stage = Column(Text, nullable=False)

    # Progress percentage (0–100)
    progress_pct = Column(Integer, nullable=False, default=0)

    # Configuration settings used for this run (stored as JSON)
    config_json = Column(JSONB, nullable=False)

    # Error message if something fails
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Track when processing starts and ends
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # Indexes for efficient querying of runs per dataset
    __table_args__ = (
        Index("ix_runs_dataset_created_at", "dataset_id", "created_at"),
        Index("ix_runs_dataset_id", "dataset_id"),
    )


# =========================
# 6) file_fingerprints
# =========================
# Stores generated fingerprints for each file during a run
class FileFingerprint(Base):
    __tablename__ = "file_fingerprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    run_id = Column(UUID(as_uuid=True), ForeignKey("runs.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False)

    # Parameters used for fingerprinting
    k = Column(Integer, nullable=False)
    w = Column(Integer, nullable=False)

    # Version of fingerprint algorithm used
    algo_version = Column(Text, nullable=False)

    # Store compressed fingerprint bytes
    fingerprint_blob = Column(BYTEA, nullable=False)

    fingerprint_count = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Ensure one fingerprint record per file per run
    __table_args__ = (
        UniqueConstraint("run_id", "file_id", name="uq_file_fingerprints_run_file"),
        Index("ix_file_fingerprints_file_id", "file_id"),
        Index("ix_file_fingerprints_run_id", "run_id"),
    )
