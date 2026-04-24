from functools import lru_cache

from tree_sitter import Language, Parser

# Provided by pip packages:
#   pip install tree-sitter-python tree-sitter-java tree-sitter-c tree-sitter-cpp tree-sitter-javascript

SUPPORTED_LANGUAGES = {"python", "java", "c", "cpp", "javascript"}

@lru_cache(maxsize=None)
def get_language(lang: str) -> Language:
    lang = (lang or "").lower().strip()
    if lang == "python":
        from tree_sitter_python import language as python_language

        return Language(python_language())
    if lang == "java":
        from tree_sitter_java import language as java_language

        return Language(java_language())
    if lang == "c":
        from tree_sitter_c import language as c_language

        return Language(c_language())
    if lang == "cpp":
        from tree_sitter_cpp import language as cpp_language

        return Language(cpp_language())
    if lang == "javascript":
        from tree_sitter_javascript import language as javascript_language

        return Language(javascript_language())
    raise ValueError(f"Unsupported language: {lang}. Supported: {sorted(SUPPORTED_LANGUAGES)}")

def make_parser(lang: str) -> Parser:
    parser = Parser()
    parser.language = get_language(lang)
    return parser
