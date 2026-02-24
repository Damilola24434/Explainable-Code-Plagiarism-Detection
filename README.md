# Explainable Code Plagiarism Detection

Senior design project for detecting likely plagiarism in student programming assignments with explainable evidence.

## Current Milestone: AST Parsing

Implemented Tree-sitter-based parsing for:
- Python
- Java

Current AST parsing pipeline features:
- Parse source code into Tree-sitter ASTs
- Collect AST nodes with byte spans (`start_byte`, `end_byte`) for traceability/explainability
- Detect syntax issues via Tree-sitter error indicators (`ERROR` / `MISSING` / root error fallback)
- JSON-safe parser output by default (optional raw Tree return for internal use)
- Optional filtering of unnamed nodes (punctuation/operators) for cleaner similarity features

Core files:
- `backend/app/pipeline/ast/languages.py`
- `backend/app/pipeline/ast/parser.py`
- `backend/app/pipeline/ast/types.py`

## Running AST Parser Tests

From the repo root:

```bash
/Users/tobygabriella/Desktop/Explainable-Code-Plagiarism-Detection/backend/.venv/bin/python -m pytest backend/tests/test_ast_parser.py -q
```

Or from `backend/` with your venv activated:

```bash
pytest tests/test_ast_parser.py -q
```

## Next Planned Milestones

- ZIP upload ingestion (extract/filter `.py` and `.java`, decode, parse per file)
- Canonicalization (identifier/literal normalization)
- Structural similarity scoring (AST-based)
- Explainable evidence output (matched AST regions / locations)
