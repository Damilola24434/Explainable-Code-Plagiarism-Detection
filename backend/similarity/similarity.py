# ============================================================
# similarity.py
# Token-based Jaccard similarity scoring between two code
# submissions using k-gram fingerprints.
#
# Returns:
#   - A score between 0.0 and 1.0
#   - A percentage overlap
#   - The set of matching fingerprint hashes (token evidence)
# ============================================================

from typing import List, Dict, Any
from similarity.thresholds import get_similarity_label


def compute_jaccard_similarity(
    fingerprints_a: List[str],
    fingerprints_b: List[str]
) -> Dict[str, Any]:
    """
    Compute Jaccard similarity between two lists of fingerprint hashes.

    Jaccard similarity is defined as:
        |A ∩ B| / |A ∪ B|

    This measures the proportion of shared k-gram fingerprints
    out of all unique fingerprints across both submissions.

    Args:
        fingerprints_a: List of SHA-256 hash strings from submission A
        fingerprints_b: List of SHA-256 hash strings from submission B

    Returns:
        A dictionary containing:
            - score (float):            Jaccard score between 0.0 and 1.0
            - percentage (float):       Score expressed as a percentage
            - matching_fingerprints     Set of hashes found in both submissions
            - total_unique (int):       Size of the union of both fingerprint sets
            - label (str):              Human-readable verdict from thresholds.py
    """
    set_a = set(fingerprints_a)
    set_b = set(fingerprints_b)

    intersection = set_a & set_b  # fingerprints shared by both submissions
    union = set_a | set_b         # all unique fingerprints across both

    if len(union) == 0:
        # Edge case: both submissions produced no fingerprints
        return {
            "score": 0.0,
            "percentage": 0.0,
            "matching_fingerprints": set(),
            "total_unique": 0,
            "label": "low"
        }

    score = len(intersection) / len(union)

    return {
        "score": round(score, 4),
        "percentage": round(score * 100, 2),
        "matching_fingerprints": intersection,
        "total_unique": len(union),
        "label": get_similarity_label(score)
    }