from pathlib import PurePosixPath


SUPPORTED_UPLOAD_EXTENSIONS = {".py", ".java"}


def should_skip_zip_entry(path: str) -> bool:
    """Drop macOS archive metadata and non-source files during upload."""
    normalized = (path or "").strip().replace("\\", "/")
    if not normalized or normalized.endswith("/"):
        return True

    parts = [part for part in PurePosixPath(normalized).parts if part not in {"", "."}]
    if not parts:
        return True
    if "__MACOSX" in parts:
        return True

    basename = parts[-1]
    if basename in {".DS_Store"} or basename.startswith("._"):
        return True

    return PurePosixPath(basename).suffix.lower() not in SUPPORTED_UPLOAD_EXTENSIONS


def group_zip_files(names: list[str]) -> dict[str, list[str]]:
    """Group zip entry paths by top-level folder (one folder = one student)."""
    groups: dict[str, list[str]] = {}
    for path in names:
        if should_skip_zip_entry(path):
            continue
        student = path.split("/")[0] if "/" in path else "root"
        groups.setdefault(student, []).append(path)
    return groups
