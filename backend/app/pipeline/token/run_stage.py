from __future__ import annotations

import json
import re
from dataclasses import dataclass
from itertools import combinations
from typing import Any, Dict, List, Optional

from app.pipeline.ast.run_stage import decode_file_content, infer_language_from_path
from similarity.fingerprint import generate_fingerprints
from similarity.kgram import generate_kgrams
from similarity.similarity import compute_jaccard_similarity
from similarity.thresholds import K_GRAM_SIZE
from similarity.tokenizer import tokenize

PYTHON_KEYWORDS = {
    "false", "none", "true", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally", "for",
    "from", "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
    "or", "pass", "raise", "return", "try", "while", "with", "yield", "range",
}

JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "continue", "default", "do", "double", "else", "enum", "extends",
    "final", "finally", "float", "for", "if", "implements", "import", "int",
    "interface", "long", "new", "package", "private", "protected", "public",
    "return", "short", "static", "switch", "this", "throw", "throws", "try",
    "void", "while", "true", "false", "null",
}


@dataclass(frozen=True)
class TokenPreparedFile:
    file_id: Any
    path: str
    language: str
    source_code: str
    tokens: List[str]
    kgrams: List[tuple[str, ...]]
    fingerprints: List[str]


def _normalized_tokens(tokens: List[str], language: str) -> List[str]:
    keywords = PYTHON_KEYWORDS if language == "python" else JAVA_KEYWORDS
    normalized: List[str] = []

    for token in tokens:
        if token in keywords:
            normalized.append(token)
        elif token.isdigit():
            normalized.append("NUM")
        elif re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token):
            normalized.append("IDENT")
        else:
            normalized.append(token)

    return normalized


def prepare_token_file(
    *,
    file_id: Any,
    path: str,
    content: bytes,
    language: str = "",
    k: int = K_GRAM_SIZE,
) -> Optional[TokenPreparedFile]:
    resolved_language = (language or "").strip().lower() or infer_language_from_path(path)
    if resolved_language not in {"python", "java"}:
        return None

    source_code = decode_file_content(content)
    if source_code is None:
        return None

    tokens = _normalized_tokens(tokenize(source_code), resolved_language)
    kgrams = generate_kgrams(tokens, k=k)
    fingerprints = generate_fingerprints(kgrams)

    return TokenPreparedFile(
        file_id=file_id,
        path=path,
        language=resolved_language,
        source_code=source_code,
        tokens=tokens,
        kgrams=kgrams,
        fingerprints=fingerprints,
    )


def serialize_fingerprints(fingerprints: List[str]) -> bytes:
    return json.dumps(fingerprints).encode("utf-8")


def compare_prepared_token_files(
    prepared_files: List[TokenPreparedFile],
    *,
    k: int = K_GRAM_SIZE,
) -> List[Dict[str, Any]]:
    comparisons: List[Dict[str, Any]] = []

    for file_a, file_b in combinations(prepared_files, 2):
        if file_a.language != file_b.language:
            continue

        result = compute_jaccard_similarity(file_a.fingerprints, file_b.fingerprints)
        shared_fingerprints = set(result["matching_fingerprints"])
        evidence = []

        for fingerprint in shared_fingerprints:
            positions_a = [idx for idx, fp in enumerate(file_a.fingerprints) if fp == fingerprint][:3]
            positions_b = [idx for idx, fp in enumerate(file_b.fingerprints) if fp == fingerprint][:3]
            evidence.append(
                {
                    "fingerprint": fingerprint,
                    "support_count": min(
                        file_a.fingerprints.count(fingerprint),
                        file_b.fingerprints.count(fingerprint),
                    ),
                    "locations_a": positions_a,
                    "locations_b": positions_b,
                }
            )

        comparisons.append(
            {
                "file_a_id": file_a.file_id,
                "file_b_id": file_b.file_id,
                "language": file_a.language,
                "fingerprint_score": result["score"],
                "overlap_count": len(shared_fingerprints),
                "matching_fingerprints": sorted(shared_fingerprints),
                "evidence": evidence,
                "method": "token_fingerprint_jaccard",
            }
        )

    comparisons.sort(key=lambda item: item["fingerprint_score"], reverse=True)
    return comparisons
