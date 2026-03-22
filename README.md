# Explainable Code Plagiarism Detection

Senior design project for detecting likely plagiarism in student programming assignments with explainable evidence.

## 🚀 Quick Start (For Teammates)

**Requirements:** Docker & Docker Compose

**3 Steps:**

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Damilola24434/Explainable-Code-Plagiarism-Detection.git
   cd Explainable-Code-Plagiarism-Detection
   ```

2. **Start everything:**
   ```bash
   docker compose up --build -d
   ```

3. **Open the app:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

**Stop the app:**
```bash
docker compose down
```

---

## Why Docker? (Why It's Easy)

✅ **No Manual Setup** — No need to install Python, Node.js, PostgreSQL, Redis separately  
✅ **Consistent Environment** — Works the same on Windows, Mac, and Linux  
✅ **One Command Start** — Everything (frontend, backend, database, worker) runs with `docker compose up --build -d`  
✅ **Zero Config** — All services are pre-configured and connected automatically  
✅ **Easy Cleanup** — One command `docker compose down` removes everything  

**For teammates:** Just install [Docker Desktop](https://www.docker.com/products/docker-desktop), clone the repo, and run the start command. That's it! No Python venv, no package installation headaches, no "it works on my machine" problems.

---
---

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

## Troubleshooting

If something goes wrong:

- **Check container status:** `docker ps`
- **View backend logs:** `docker logs plagiarism-backend --tail 100`
- **Restart everything:** `docker compose down && docker compose up --build -d`

---

## Development

## Team Run Guide (Detailed)

## Next Planned Milestones

- ZIP upload ingestion (extract/filter `.py` and `.java`, decode, parse per file)
- Canonicalization (identifier/literal normalization)
- Structural similarity scoring (AST-based)
- Explainable evidence output (matched AST regions / locations)
