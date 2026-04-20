from app.pipeline.ast.run_stage import (
    compare_prepared_files,
    decode_file_content,
    infer_language_from_path,
    prepare_ast_file,
)


def test_infer_language_from_path_supports_configured_languages():
    assert infer_language_from_path("studentA/main.py") == "python"
    assert infer_language_from_path("studentB/src/Main.java") == "java"
    assert infer_language_from_path("studentB/src/main.c") == "c"
    assert infer_language_from_path("studentC/src/main.cpp") == "cpp"
    assert infer_language_from_path("studentC/include/main.hpp") == "cpp"
    assert infer_language_from_path("studentD/app.js") == "javascript"
    assert infer_language_from_path("studentD/component.jsx") == "javascript"
    assert infer_language_from_path("studentC/notes.txt") is None


def test_decode_file_content_decodes_utf8_source():
    content = "def add(a, b):\n    return a + b\n".encode("utf-8")
    assert decode_file_content(content) == "def add(a, b):\n    return a + b\n"


def test_prepare_ast_file_builds_handoff_from_stored_file_bytes():
    prepared = prepare_ast_file(
        file_id="file-a",
        path="studentA/add.py",
        content=b"def add(a, b):\n    return a + b\n",
    )

    assert prepared is not None
    assert prepared.language == "python"
    assert prepared.handoff["feature_version"] == "ast-handoff-v1"
    assert prepared.handoff["token_count"] > 0


def test_compare_prepared_files_ranks_similar_python_files_higher():
    file_a = prepare_ast_file(
        file_id="file-a",
        path="studentA/add.py",
        content=(
            "def add(a, b):\n"
            "    total = a + 1\n"
            "    if total > 0:\n"
            "        return total + b\n"
            "    return 0\n"
        ).encode("utf-8"),
    )
    file_b = prepare_ast_file(
        file_id="file-b",
        path="studentB/add.py",
        content=(
            "def sum_values(x, y):\n"
            "    out = x + 999\n"
            "    if out > 0:\n"
            "        return out + y\n"
            "    return 0\n"
        ).encode("utf-8"),
    )
    file_c = prepare_ast_file(
        file_id="file-c",
        path="studentC/factorial.py",
        content=(
            "def factorial(n):\n"
            "    if n <= 1:\n"
            "        return 1\n"
            "    result = 1\n"
            "    for i in range(2, n + 1):\n"
            "        result *= i\n"
            "    return result\n"
        ).encode("utf-8"),
    )

    comparisons = compare_prepared_files([file_a, file_b, file_c], n=3)
    assert len(comparisons) == 3
    assert comparisons[0]["file_a_id"] == "file-a"
    assert comparisons[0]["file_b_id"] == "file-b"
    assert comparisons[0]["ast_score"] > comparisons[-1]["ast_score"]
    assert len(comparisons[0]["evidence"]) > 0


def test_compare_prepared_files_can_limit_to_candidate_pairs():
    file_a = prepare_ast_file(
        file_id="file-a",
        path="studentA/add.py",
        content=b"def add(a, b):\n    return a + b\n",
    )
    file_b = prepare_ast_file(
        file_id="file-b",
        path="studentB/add.py",
        content=b"def sum_values(x, y):\n    return x + y\n",
    )
    file_c = prepare_ast_file(
        file_id="file-c",
        path="studentC/factorial.py",
        content=b"def factorial(n):\n    return 1 if n <= 1 else n * factorial(n - 1)\n",
    )

    comparisons = compare_prepared_files(
        [file_a, file_b, file_c],
        n=3,
        candidate_pairs={("file-a", "file-b")},
    )

    assert len(comparisons) == 1
    assert comparisons[0]["file_a_id"] == "file-a"
    assert comparisons[0]["file_b_id"] == "file-b"
