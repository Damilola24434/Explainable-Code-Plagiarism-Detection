from app.pipeline.ast.parser import parse_and_collect

py_code = "def add(a,b):\n    return a+b\n"
java_code = "class A { int add(int a,int b){ return a+b; } }"

py = parse_and_collect(py_code, "python")
jv = parse_and_collect(java_code, "java")

print("PY nodes:", len(py["nodes"]), "errors:", py["error_count"])
print("JAVA nodes:", len(jv["nodes"]), "errors:", jv["error_count"])

# Show first few nodes so you can confirm byte offsets exist
print("PY sample nodes:", py["nodes"][:5])
print("JAVA sample nodes:", jv["nodes"][:5])
