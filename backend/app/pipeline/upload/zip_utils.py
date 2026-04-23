from pathlib import PurePosixPath
from typing import Optional


SUPPORTED_UPLOAD_EXTENSIONS = {
    ".py",
    ".java",
    ".c",
    ".cpp",
    ".cc",
    ".cxx",
    ".hpp",
    ".hh",
    ".hxx",
    ".h",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
}


def zip_entry_skip_reason(path: str) -> Optional[str]:
    """Return a user-facing skip reason, or None when the entry is supported."""
    normalized = (path or "").strip().replace("\\", "/")
    if not normalized:
        return "empty path"
    if normalized.endswith("/"):
        return "directory"

    parts = [part for part in PurePosixPath(normalized).parts if part not in {"", "."}]
    if not parts:
        return "empty path"
    if "__MACOSX" in parts:
        return "macOS metadata"

    basename = parts[-1]
    if basename == ".DS_Store" or basename.startswith("._"):
        return "system metadata file"

    suffix = PurePosixPath(basename).suffix.lower()
    if suffix not in SUPPORTED_UPLOAD_EXTENSIONS:
        return "unsupported file type"

    return None


def should_skip_zip_entry(path: str) -> bool:
    """Drop macOS archive metadata and non-source files during upload."""
    return zip_entry_skip_reason(path) is not None


def group_zip_files(names: list[str]) -> dict[str, list[str]]:
    """Group zip entry paths by top-level folder (one folder = one student)."""
    groups: dict[str, list[str]] = {}
    for path in names:
        if should_skip_zip_entry(path):
            continue
        student = path.split("/")[0] if "/" in path else "root"
        groups.setdefault(student, []).append(path)
    return groups
