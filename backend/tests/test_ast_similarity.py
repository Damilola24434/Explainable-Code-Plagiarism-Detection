from app.pipeline.ast.parser import parse_and_collect
from app.pipeline.ast.similarity import compare_feature_handoffs


def _build_handoff(code: str, language: str, file_path: str):
    result = parse_and_collect(
        code,
        language,
        include_unnamed_nodes=False,
        canonicalize=True,
        normalize_statements=True,
        build_handoff=True,
        file_path=file_path,
    )
    return result["feature_handoff"]


def test_similarity_ranks_renamed_python_pair_above_unrelated_pair():
    similar_a = (
        "def add(a, b):\n"
        "    total = a + 1\n"
        "    if total > 0:\n"
        "        return total + b\n"
        "    return 0\n"
    )
    similar_b = (
        "def sum_values(x, y):\n"
        "    out = x + 999\n"
        "    if out > 0:\n"
        "        return out + y\n"
        "    return 0\n"
    )
    unrelated = (
        "def factorial(n):\n"
        "    if n <= 1:\n"
        "        return 1\n"
        "    result = 1\n"
        "    for i in range(2, n + 1):\n"
        "        result *= i\n"
        "    return result\n"
    )

    h_a = _build_handoff(similar_a, "python", "A.py")
    h_b = _build_handoff(similar_b, "python", "B.py")
    h_c = _build_handoff(unrelated, "python", "C.py")

    sim_score = compare_feature_handoffs(h_a, h_b, n=3)["score"]
    diff_score = compare_feature_handoffs(h_a, h_c, n=3)["score"]

    assert sim_score > diff_score
    assert sim_score > 0.45


def test_similarity_evidence_contains_match_locations_for_both_files():
    code_a = "def add(a, b):\n    total = a + b\n    return total\n"
    code_b = "def sum_values(x, y):\n    out = x + y\n    return out\n"

    h_a = _build_handoff(code_a, "python", "studentA/add.py")
    h_b = _build_handoff(code_b, "python", "studentB/add.py")

    result = compare_feature_handoffs(h_a, h_b, n=3)
    assert result["method"] == "ast_node_ngrams_jaccard"
    assert result["matched_ngrams"] > 0
    assert result["score"] > 0
    assert len(result["evidence"]) > 0

    sample = result["evidence"][0]
    assert "ngram" in sample
    assert "locations_a" in sample
    assert "locations_b" in sample
    assert len(sample["locations_a"]) > 0
    assert len(sample["locations_b"]) > 0

    loc_a = sample["locations_a"][0]
    loc_b = sample["locations_b"][0]
    assert loc_a["start_byte"] <= loc_a["end_byte"]
    assert loc_b["start_byte"] <= loc_b["end_byte"]
