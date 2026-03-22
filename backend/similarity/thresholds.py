# ============================================================
# thresholds.py
# Configurable similarity threshold constants for token-based
# plagiarism detection using Jaccard similarity.
#
# These values determine how similarity scores are interpreted
# and labelled in the detection pipeline.
# ============================================================

# Minimum Jaccard score to flag a pair as potentially similar.
# Pairs below this threshold are considered distinct and ignored.
SIMILARITY_THRESHOLD_MIN: float = 0.20

# Score at or above this value is considered suspicious and
# worth manual review by an instructor.
SIMILARITY_THRESHOLD_SUSPICIOUS: float = 0.40

# Score at or above this value is considered a likely plagiarism case.
SIMILARITY_THRESHOLD_HIGH: float = 0.70

# Labels mapped to threshold bands for reporting purposes.
# Used by the scoring engine to attach a human-readable verdict.
SIMILARITY_LABELS = {
    "low":        (0.00, SIMILARITY_THRESHOLD_MIN),        # Not similar
    "moderate":   (SIMILARITY_THRESHOLD_MIN, SIMILARITY_THRESHOLD_SUSPICIOUS),  # Weak overlap
    "suspicious": (SIMILARITY_THRESHOLD_SUSPICIOUS, SIMILARITY_THRESHOLD_HIGH), # Worth reviewing
    "high":       (SIMILARITY_THRESHOLD_HIGH, 1.01),       # Likely plagiarism
}


def get_similarity_label(score: float) -> str:
    """
    Return a human-readable label for a given Jaccard similarity score
    based on the defined threshold bands.

    Args:
        score: A float between 0.0 and 1.0

    Returns:
        A label string: 'low', 'moderate', 'suspicious', or 'high'
    """
    for label, (lower, upper) in SIMILARITY_LABELS.items():
        if lower <= score < upper:
            return label
    return "high"  # Fallback for score == 1.0