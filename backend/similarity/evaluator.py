# ============================================================
# evaluator.py
# Token-based similarity evaluation module.
#
# This is the main callable entry point for the token-based
# plagiarism detection pipeline. It accepts two raw code
# strings and returns a fully structured similarity result.
#
# Designed to plug directly into Dami's TOKENS stage
# in the Celery pipeline as a drop-in replacement for the
# placeholder logic.
#
# Pipeline:
#   raw code → tokenize → k-grams → fingerprints → Jaccard score
#
# Returns a structured dict matching the backend's result
# schema so it can be persisted to the database and consumed
# by the frontend results view.
# ============================================================

from typing import List, Dict, Any
from similarity.tokenizer import tokenize
from similarity.kgram import generate_kgrams
from similarity.fingerprint import generate_fingerprints
from similarity.similarity import compute_jaccard_similarity
from similarity.thresholds import get_similarity_label, K_GRAM_SIZE


# ============================================================
# SINGLE PAIR EVALUATION
# Compares two code submissions and returns a structured
# similarity result.
# ============================================================

def evaluate_pair(
    code_a: str,
    code_b: str,
    submission_id_a: str = "submission_a",
    submission_id_b: str = "submission_b",
    k: int = K_GRAM_SIZE,
) -> Dict[str, Any]:
    """
    Run the full token-based similarity pipeline on two
    raw code strings.

    Args:
        code_a:           Raw source code of submission A
        code_b:           Raw source code of submission B
        submission_id_a:  Identifier for submission A (filename or ID)
        submission_id_b:  Identifier for submission B (filename or ID)
        k:                K-gram window size (defaults to thresholds.py value)

    Returns:
        A structured dict containing:
            - submission_a (str):         ID of submission A
            - submission_b (str):         ID of submission B
            - score (float):              Jaccard score 0.0 to 1.0
            - percentage (float):         Score as a percentage
            - label (str):                Verdict: low/moderate/suspicious/high
            - matching_fingerprint_count: Number of shared fingerprints
            - total_unique_fingerprints:  Size of the union of fingerprint sets
            - token_count_a (int):        Number of tokens in submission A
            - token_count_b (int):        Number of tokens in submission B
            - kgram_count_a (int):        Number of k-grams in submission A
            - kgram_count_b (int):        Number of k-grams in submission B
            - k (int):                    K-gram size used
            - matching_fingerprints (set): Shared fingerprint hashes
              (used for evidence mapping — strip before JSON serialization)
    """
    # Step 1 — Tokenize
    tokens_a = tokenize(code_a)
    tokens_b = tokenize(code_b)

    # Step 2 — Generate k-grams
    kgrams_a = generate_kgrams(tokens_a, k=k)
    kgrams_b = generate_kgrams(tokens_b, k=k)

    # Step 3 — Generate fingerprints
    fingerprints_a = generate_fingerprints(kgrams_a)
    fingerprints_b = generate_fingerprints(kgrams_b)

    # Step 4 — Compute Jaccard similarity
    result = compute_jaccard_similarity(fingerprints_a, fingerprints_b)

    # Step 5 — Build structured output
    return {
        "submission_a": submission_id_a,
        "submission_b": submission_id_b,
        "score": result["score"],
        "percentage": result["percentage"],
        "label": result["label"],
        "matching_fingerprint_count": len(result["matching_fingerprints"]),
        "total_unique_fingerprints": result["total_unique"],
        "token_count_a": len(tokens_a),
        "token_count_b": len(tokens_b),
        "kgram_count_a": len(kgrams_a),
        "kgram_count_b": len(kgrams_b),
        "k": k,
        "matching_fingerprints": result["matching_fingerprints"],
    }


# ============================================================
# BATCH EVALUATION
# Compares all possible pairs from a list of submissions.
# This is what Dami's TOKENS stage will call with the full set of submissions in a run.
# ============================================================

def evaluate_batch(
    submissions: List[Dict[str, str]],
    k: int = K_GRAM_SIZE,
) -> List[Dict[str, Any]]:
    """
    Compare all unique pairs from a list of submissions.

    Args:
        submissions: List of dicts, each with:
                        - id (str):   submission identifier
                        - code (str): raw source code
        k:           K-gram window size

    Returns:
        List of result dicts from evaluate_pair(), one per
        unique pair, sorted by score descending so the most
        suspicious pairs appear first.

    Example input:
        [
            {"id": "student_01.py", "code": "def foo(): ..."},
            {"id": "student_02.py", "code": "def bar(): ..."},
            {"id": "student_03.py", "code": "def foo(): ..."},
        ]
    """
    results = []

    # Generate all unique pairs (no duplicates, no self-comparison)
    for i in range(len(submissions)):
        for j in range(i + 1, len(submissions)):
            sub_a = submissions[i]
            sub_b = submissions[j]

            result = evaluate_pair(
                code_a=sub_a["code"],
                code_b=sub_b["code"],
                submission_id_a=sub_a["id"],
                submission_id_b=sub_b["id"],
                k=k,
            )
            results.append(result)

    # Sort by score descending — most suspicious pairs first
    results.sort(key=lambda r: r["score"], reverse=True)

    return results


# ============================================================
# JSON-SAFE SERIALIZER
# Strips the matching_fingerprints set (not JSON serializable)
# and returns a clean dict ready for database persistence
# or API response.
# Call this before passing results to Dami's pipeline.
# ============================================================

def serialize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a JSON-serializable version of an evaluate_pair()
    result by removing the matching_fingerprints set.

    Args:
        result: Output dict from evaluate_pair()

    Returns:
        Clean dict safe for JSON serialization and DB storage
    """
    return {k: v for k, v in result.items() if k != "matching_fingerprints"}


def serialize_batch(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Serialize all results in a batch for DB persistence or
    API response.

    Args:
        results: Output list from evaluate_batch()

    Returns:
        List of clean, JSON-serializable result dicts
    """
    return [serialize_result(r) for r in results]