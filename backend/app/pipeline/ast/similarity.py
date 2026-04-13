from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Sequence, Tuple


def _extract_ngrams(tokens: Sequence[str], n: int) -> List[Tuple[str, ...]]:
    if n <= 0:
        raise ValueError("n must be >= 1")
    if len(tokens) < n:
        return []
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _index_ngram_positions(ngrams: Sequence[Tuple[str, ...]]) -> Dict[Tuple[str, ...], List[int]]:
    positions: Dict[Tuple[str, ...], List[int]] = defaultdict(list)
    for i, ng in enumerate(ngrams):
        positions[ng].append(i)
    return dict(positions)


def _window_span(token_spans: Sequence[Dict[str, Any]], start_index: int, n: int) -> Dict[str, Any]:
    window = token_spans[start_index : start_index + n]
    start_byte = min(item["start_byte"] for item in window)
    end_byte = max(item["end_byte"] for item in window)
    return {
        "token_start_index": start_index,
        "token_end_index": start_index + n - 1,
        "start_byte": start_byte,
        "end_byte": end_byte,
    }


def compare_feature_handoffs(
    handoff_a: Dict[str, Any],
    handoff_b: Dict[str, Any],
    n: int = 3,
    max_evidence_per_ngram: int = 3,
    max_evidence_items: int = 15,
) -> Dict[str, Any]:
    """
    Compare two AST feature handoff payloads using node n-gram Jaccard similarity.

    Returns:
    - score: Jaccard similarity of unique n-gram sets
    - matched_ngrams: count of shared unique n-grams
    - evidence: matched n-gram snippets + byte span locations in both files
    """
    tokens_a = handoff_a.get("feature_tokens", [])
    tokens_b = handoff_b.get("feature_tokens", [])
    spans_a = handoff_a.get("token_spans", [])
    spans_b = handoff_b.get("token_spans", [])

    ngrams_a = _extract_ngrams(tokens_a, n)
    ngrams_b = _extract_ngrams(tokens_b, n)
    set_a = set(ngrams_a)
    set_b = set(ngrams_b)

    if not set_a and not set_b:
        score = 1.0
        shared = set()
    else:
        shared = set_a & set_b
        union = set_a | set_b
        score = len(shared) / len(union) if union else 0.0

    idx_a = _index_ngram_positions(ngrams_a)
    idx_b = _index_ngram_positions(ngrams_b)

    evidence: List[Dict[str, Any]] = []
    for ng in sorted(shared):
        a_positions = idx_a.get(ng, [])[:max_evidence_per_ngram]
        b_positions = idx_b.get(ng, [])[:max_evidence_per_ngram]

        evidence.append(
            {
                "ngram": list(ng),
                "support_count": min(len(idx_a.get(ng, [])), len(idx_b.get(ng, []))),
                "locations_a": [_window_span(spans_a, pos, n) for pos in a_positions],
                "locations_b": [_window_span(spans_b, pos, n) for pos in b_positions],
            }
        )

    evidence.sort(key=lambda item: item["support_count"], reverse=True)
    evidence = evidence[:max_evidence_items]

    return {
        "method": "ast_node_ngrams_jaccard",
        "n": n,
        "score": score,
        "matched_ngrams": len(shared),
        "ngrams_a": len(set_a),
        "ngrams_b": len(set_b),
        "parse_ok_a": handoff_a.get("parse_ok", False),
        "parse_ok_b": handoff_b.get("parse_ok", False),
        "evidence": evidence,
    }
