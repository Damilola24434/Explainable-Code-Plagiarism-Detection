from app.pipeline.ast.parser import parse_and_collect

def assert_spans_valid(code: str, nodes):
    encoded_len = len(code.encode("utf-8"))
    assert encoded_len > 0
    for n in nodes[:200]:  # limit for speed
        assert 0 <= n.start_byte <= n.end_byte <= encoded_len

def test_python_simple_function_parses():
    code = "def add(a, b):\n    return a + b\n"
    result = parse_and_collect(code, "python")
    assert result["language"] == "python"
    assert result["root_type"] == "module"
    assert result["error_count"] == 0
    assert result["node_count"] == len(result["nodes"])
    assert result["include_unnamed_nodes"] is True
    assert len(result["nodes"]) > 0
    assert "tree" not in result
    assert_spans_valid(code, result["nodes"])

def test_java_simple_class_parses():
    code = "class A { int add(int a, int b) { return a + b; } }"
    result = parse_and_collect(code, "java")
    assert result["language"] == "java"
    assert result["root_type"] == "program"
    assert result["error_count"] == 0
    assert result["node_count"] == len(result["nodes"])
    assert result["include_unnamed_nodes"] is True
    assert len(result["nodes"]) > 0
    assert "tree" not in result
    assert_spans_valid(code, result["nodes"])

def test_python_complex_realistic_constructs():
    code = (
        "class Student:\n"
        "    def __init__(self, name, grades=None):\n"
        "        self.name = name\n"
        "        self.grades = grades or []\n\n"
        "    def avg(self):\n"
        "        total = 0\n"
        "        for g in self.grades:\n"
        "            if g < 0:\n"
        "                continue\n"
        "            total += g\n"
        "        return total / len(self.grades) if self.grades else 0\n"
    )
    result = parse_and_collect(code, "python")
    assert result["error_count"] == 0
    assert len(result["nodes"]) > 0
    assert_spans_valid(code, result["nodes"])

def test_java_complex_realistic_constructs():
    code = (
        "import java.util.*;\n"
        "class Student {\n"
        "  private String name;\n"
        "  private List<Integer> grades;\n"
        "  Student(String name) { this.name = name; this.grades = new ArrayList<>(); }\n"
        "  double avg() {\n"
        "    int total = 0;\n"
        "    for (int g : grades) {\n"
        "      if (g < 0) continue;\n"
        "      total += g;\n"
        "    }\n"
        "    return grades.size() == 0 ? 0 : ((double) total) / grades.size();\n"
        "  }\n"
        "}\n"
    )
    result = parse_and_collect(code, "java")
    assert result["error_count"] == 0
    assert len(result["nodes"]) > 0
    assert_spans_valid(code, result["nodes"])

def test_python_bad_syntax_detects_error_nodes():
    code = "def broken(:\n  return 1\n"
    result = parse_and_collect(code, "python")
    assert result["error_count"] > 0
    assert len(result["nodes"]) > 0
    assert_spans_valid(code, result["nodes"])

def test_java_bad_syntax_detects_error_nodes():
    code = "class A { int f( { return 1; } }"
    result = parse_and_collect(code, "java")
    assert result["error_count"] > 0
    assert len(result["nodes"]) > 0
    assert_spans_valid(code, result["nodes"])

def test_include_tree_opt_in_returns_raw_tree():
    code = "def add(a, b):\n    return a + b\n"
    result = parse_and_collect(code, "python", include_tree=True)
    assert "tree" in result
    assert result["tree"].root_node.type == "module"
    # Demo output for presentation (visible with: pytest -s)
    root = result["tree"].root_node
    print("Parsed root node:", root.type)
    print("Root byte span:", root.start_byte, root.end_byte)
    print("First-level child types:", [child.type for child in root.children])
    print("Raw tree object:", result["tree"])

    def dump(node, depth=0, max_depth=3):
        if depth > max_depth:
            return
        indent = "  " * depth
        print(f"{indent}- {node.type} [{node.start_byte}, {node.end_byte}]")
        for child in node.children:
            dump(child, depth + 1, max_depth=max_depth)

    print("Tree preview (depth <= 3):")
    dump(root, max_depth=3)

def test_can_exclude_unnamed_nodes_for_similarity_signal():
    code = "def add(a, b):\n    return a + b\n"
    with_unnamed = parse_and_collect(code, "python", include_unnamed_nodes=True)
    named_only = parse_and_collect(code, "python", include_unnamed_nodes=False)

    assert with_unnamed["node_count"] >= named_only["node_count"]
    assert named_only["include_unnamed_nodes"] is False
    assert named_only["node_count"] > 0

    with_types = {n.type for n in with_unnamed["nodes"]}
    named_types = {n.type for n in named_only["nodes"]}
    assert "(" in with_types or ")" in with_types or ":" in with_types
    assert "(" not in named_types
    assert ")" not in named_types
    assert ":" not in named_types

def test_python_canonicalization_normalizes_identifiers_and_literals():
    code_a = "def add(a, b):\n    total = a + 1\n    return total + b\n"
    code_b = "def sum_values(x, y):\n    out = x + 999\n    return out + y\n"

    result_a = parse_and_collect(code_a, "python", include_unnamed_nodes=False, canonicalize=True)
    result_b = parse_and_collect(code_b, "python", include_unnamed_nodes=False, canonicalize=True)

    labels_a = [n.type for n in result_a["canonical_nodes"]]
    labels_b = [n.type for n in result_b["canonical_nodes"]]

    assert labels_a == labels_b
    assert "NUM_LIT" in labels_a
    assert any(label.startswith("IDENT_") for label in labels_a)
    assert result_a["identifier_symbol_count"] > 0

def test_java_canonicalization_normalizes_identifiers_and_literals():
    code_a = "class A { int f(int a){ int t = a + 1; return t; } }"
    code_b = "class B { int g(int x){ int result = x + 250; return result; } }"

    result_a = parse_and_collect(code_a, "java", include_unnamed_nodes=False, canonicalize=True)
    result_b = parse_and_collect(code_b, "java", include_unnamed_nodes=False, canonicalize=True)

    labels_a = [n.type for n in result_a["canonical_nodes"]]
    labels_b = [n.type for n in result_b["canonical_nodes"]]

    assert labels_a == labels_b
    assert "NUM_LIT" in labels_a
    assert any(label.startswith("IDENT_") for label in labels_a)

def test_canonicalization_is_opt_in():
    code = "def add(a, b):\n    return a + b\n"
    default_result = parse_and_collect(code, "python")
    canonical_result = parse_and_collect(code, "python", canonicalize=True)

    assert "canonical_nodes" not in default_result
    assert canonical_result["canonical_node_count"] == len(canonical_result["canonical_nodes"])

def test_statement_normalization_python_maps_to_stmt_families():
    code = (
        "def add(a, b):\n"
        "    total = a + b\n"
        "    if total > 0:\n"
        "        return total\n"
        "    return 0\n"
    )
    result = parse_and_collect(
        code,
        "python",
        include_unnamed_nodes=False,
        canonicalize=True,
        normalize_statements=True,
    )
    labels = {n.type for n in result["canonical_nodes"]}

    assert result["normalize_statements"] is True
    assert "STMT_FUNCTION_DEF" in labels
    assert "STMT_ASSIGN" in labels
    assert "STMT_IF" in labels
    assert "STMT_RETURN" in labels
    assert "return_statement" not in labels
    assert "assignment" not in labels

def test_statement_normalization_java_maps_to_stmt_families():
    code = "class A { int add(int a, int b){ int total = a + b; if (total > 0) return total; return 0; } }"
    result = parse_and_collect(
        code,
        "java",
        include_unnamed_nodes=False,
        canonicalize=True,
        normalize_statements=True,
    )
    labels = {n.type for n in result["canonical_nodes"]}

    assert "STMT_CLASS_DEF" in labels
    assert "STMT_FUNCTION_DEF" in labels
    assert "STMT_ASSIGN" in labels
    assert "STMT_IF" in labels
    assert "STMT_RETURN" in labels

def test_statement_normalization_keeps_distinct_control_flow_families():
    code = (
        "def demo(nums):\n"
        "    total = 0\n"
        "    for n in nums:\n"
        "        if n > 0:\n"
        "            total += n\n"
        "    while total < 10:\n"
        "        total += 1\n"
        "    return total\n"
    )
    result = parse_and_collect(
        code,
        "python",
        include_unnamed_nodes=False,
        canonicalize=True,
        normalize_statements=True,
    )
    labels = {n.type for n in result["canonical_nodes"]}

    assert "STMT_IF" in labels
    assert "STMT_FOR" in labels
    assert "STMT_WHILE" in labels
    assert "STMT_IF" != "STMT_FOR"
    assert "STMT_FOR" != "STMT_WHILE"

def test_statement_normalization_requires_canonicalize():
    code = "def add(a, b):\n    return a + b\n"
    try:
        parse_and_collect(code, "python", normalize_statements=True)
        assert False, "Expected ValueError when normalize_statements=True without canonicalize=True"
    except ValueError as exc:
        assert "requires canonicalize=True" in str(exc)

def test_build_handoff_requires_canonicalize():
    code = "def add(a, b):\n    return a + b\n"
    try:
        parse_and_collect(code, "python", build_handoff=True)
        assert False, "Expected ValueError when build_handoff=True without canonicalize=True"
    except ValueError as exc:
        assert "build_handoff=True requires canonicalize=True" in str(exc)

def test_feature_handoff_contains_tokens_and_explainability_metadata():
    code = "def add(a, b):\n    total = a + b\n    return total\n"
    result = parse_and_collect(
        code,
        "python",
        include_unnamed_nodes=False,
        canonicalize=True,
        normalize_statements=True,
        build_handoff=True,
        file_path="studentA/add.py",
    )
    handoff = result["feature_handoff"]

    assert handoff["feature_version"] == "ast-handoff-v1"
    assert handoff["language"] == "python"
    assert handoff["file_path"] == "studentA/add.py"
    assert handoff["token_count"] == len(handoff["feature_tokens"])
    assert handoff["token_count"] == len(handoff["token_spans"])
    assert handoff["uses_canonical_nodes"] is True
    assert handoff["uses_statement_normalization"] is True
    assert handoff["parse_ok"] is True
    assert handoff["error_count"] == 0

    first_span = handoff["token_spans"][0]
    assert "token_index" in first_span
    assert "start_byte" in first_span
    assert "end_byte" in first_span
    assert "node_type" in first_span
    assert "parent_type" in first_span

def test_feature_handoff_is_stable_across_renamed_python_submissions():
    code_a = "def add(a, b):\n    total = a + 5\n    return total + b\n"
    code_b = "def sum_values(x, y):\n    out = x + 999\n    return out + y\n"

    a = parse_and_collect(
        code_a,
        "python",
        include_unnamed_nodes=False,
        canonicalize=True,
        normalize_statements=True,
        build_handoff=True,
    )
    b = parse_and_collect(
        code_b,
        "python",
        include_unnamed_nodes=False,
        canonicalize=True,
        normalize_statements=True,
        build_handoff=True,
    )

    assert a["feature_handoff"]["feature_tokens"] == b["feature_handoff"]["feature_tokens"]
