from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Dict, List, Optional

from .parser import parse_and_collect
from .similarity import compare_feature_handoffs


SUPPORTED_LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".java": "java",
}


@dataclass(frozen=True)
class ASTPreparedFile:
    file_id: Any
    path: str
    language: str
    source_code: str
    handoff: Dict[str, Any]


def infer_language_from_path(path: str) -> Optional[str]:
    lowered = (path or "").lower()
    for ext, language in SUPPORTED_LANGUAGE_EXTENSIONS.items():
        if lowered.endswith(ext):
            return language
    return None


def decode_file_content(content: bytes) -> Optional[str]:
    if content is None:
        return None

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


def prepare_ast_file(
    *,
    file_id: Any,
    path: str,
    content: bytes,
    language: str = "",
) -> Optional[ASTPreparedFile]:
    resolved_language = (language or "").strip().lower() or infer_language_from_path(path)
    if resolved_language not in {"python", "java"}:
        return None

    source_code = decode_file_content(content)
    if source_code is None:
        return None

    parsed = parse_and_collect(
        source_code,
        resolved_language,
        include_unnamed_nodes=False,
        canonicalize=True,
        normalize_statements=True,
        build_handoff=True,
        file_path=path,
    )

    return ASTPreparedFile(
        file_id=file_id,
        path=path,
        language=resolved_language,
        source_code=source_code,
        handoff=parsed["feature_handoff"],
    )


def compare_prepared_files(
    prepared_files: List[ASTPreparedFile],
    *,
    n: int = 3,
    candidate_pairs: Optional[set[tuple[str, str]]] = None,
) -> List[Dict[str, Any]]:
    comparisons: List[Dict[str, Any]] = []

    for file_a, file_b in combinations(prepared_files, 2):
        if file_a.language != file_b.language:
            continue
        pair_key = (str(file_a.file_id), str(file_b.file_id))
        if candidate_pairs is not None and pair_key not in candidate_pairs:
            continue

        result = compare_feature_handoffs(file_a.handoff, file_b.handoff, n=n)
        comparisons.append(
            {
                "file_a_id": file_a.file_id,
                "file_b_id": file_b.file_id,
                "language": file_a.language,
                "ast_score": result["score"],
                "evidence": result["evidence"],
                "matched_ngrams": result["matched_ngrams"],
                "method": result["method"],
            }
        )

    comparisons.sort(key=lambda item: item["ast_score"], reverse=True)
    return comparisons
