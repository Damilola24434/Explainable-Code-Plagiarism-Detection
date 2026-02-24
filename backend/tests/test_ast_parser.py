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
