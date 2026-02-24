from functools import lru_cache

from tree_sitter import Language, Parser

# Provided by pip packages:
#   pip install tree-sitter-python tree-sitter-java
from tree_sitter_python import language as python_language
from tree_sitter_java import language as java_language

SUPPORTED_LANGUAGES = {"python", "java"}

@lru_cache(maxsize=None)
def get_language(lang: str) -> Language:
    lang = (lang or "").lower().strip()
    if lang == "python":
        return Language(python_language())
    if lang == "java":
        return Language(java_language())
    raise ValueError(f"Unsupported language: {lang}. Supported: {sorted(SUPPORTED_LANGUAGES)}")

def make_parser(lang: str) -> Parser:
    parser = Parser()
    parser.language = get_language(lang)
    return parser
