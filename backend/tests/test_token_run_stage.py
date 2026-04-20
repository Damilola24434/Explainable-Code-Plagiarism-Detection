from app.pipeline.token.run_stage import (
    compare_prepared_token_files,
    prepare_token_file,
    serialize_fingerprints,
)


def test_prepare_token_file_extracts_tokens_and_fingerprints():
    prepared = prepare_token_file(
        file_id="file-a",
        path="studentA/add.py",
        content=b"def add(a, b):\n    return a + b\n",
        k=3,
    )

    assert prepared is not None
    assert prepared.language == "python"
    assert len(prepared.tokens) > 0
    assert len(prepared.fingerprints) > 0


def test_prepare_token_file_supports_c_cpp_and_javascript_extensions():
    c = prepare_token_file(
        file_id="c-a",
        path="studentA/main.c",
        content=b"int add(int a, int b) { return a + b; }\n",
        k=3,
    )
    cpp = prepare_token_file(
        file_id="cpp-a",
        path="studentA/main.cpp",
        content=b"int add(int a, int b) { return a + b; }\n",
        k=3,
    )
    js = prepare_token_file(
        file_id="js-a",
        path="studentB/app.js",
        content=b"function add(a, b) { return a + b; }\n",
        k=3,
    )

    assert c is not None
    assert c.language == "c"
    assert "int" in c.tokens
    assert "IDENT" in c.tokens
    assert cpp is not None
    assert cpp.language == "cpp"
    assert "int" in cpp.tokens
    assert "IDENT" in cpp.tokens
    assert js is not None
    assert js.language == "javascript"
    assert "function" in js.tokens
    assert "IDENT" in js.tokens


def test_compare_prepared_token_files_ranks_similar_pair_higher():
    file_a = prepare_token_file(
        file_id="file-a",
        path="studentA/add.py",
        content=b"def add(a, b):\n    total = a + 1\n    return total + b\n",
        k=3,
    )
    file_b = prepare_token_file(
        file_id="file-b",
        path="studentB/add.py",
        content=b"def sum_values(x, y):\n    out = x + 999\n    return out + y\n",
        k=3,
    )
    file_c = prepare_token_file(
        file_id="file-c",
        path="studentC/factorial.py",
        content=b"def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n",
        k=3,
    )

    comparisons = compare_prepared_token_files([file_a, file_b, file_c], k=3)

    assert len(comparisons) == 3
    assert comparisons[0]["file_a_id"] == "file-a"
    assert comparisons[0]["file_b_id"] == "file-b"
    assert comparisons[0]["fingerprint_score"] > comparisons[-1]["fingerprint_score"]
    assert len(comparisons[0]["evidence"]) > 0


def test_serialize_fingerprints_returns_bytes():
    payload = serialize_fingerprints(["a", "b", "c"])
    assert isinstance(payload, bytes)
    assert b"[" in payload
