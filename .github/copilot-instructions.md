# Copilot instructions for Explainable-Code-Plagiarism-Detection

Purpose
- Help AI coding agents become productive quickly in this repository by highlighting architecture, developer workflows, conventions, and concrete commands.

Big picture
- Backend: FastAPI app under `backend/app`. Entrypoint: `backend/app/main.py` (FastAPI `app`).
- DB: SQLAlchemy declarative `Base` and session in `backend/app/core/db.py`. `DATABASE_URL` is required via `.env`.
- Models: schema definitions live in `backend/app/models/models.py` (collections, datasets, submissions, files, runs, fingerprints, candidate_pairs, pair_results, evidence, reports).
- Schema bootstrapping: `backend/create_tables.py` imports `app.models.models` and calls `Base.metadata.create_all(bind=engine)`.
- Pipeline: AST parsing utilities under `backend/app/pipeline/ast` using Tree-sitter. Key files: `parser.py`, `languages.py`, `types.py`.
- Frontend: Vite + React app in `frontend/` that talks to backend API under `/api/*`.

What to know before editing
- Always run the backend from the `backend/` folder (module imports assume `app.` package). Example env and commands below.
- The project expects PostgreSQL (models use `JSONB`, `BYTEA`, and `UUID` from `postgresql` dialect).
- Authentication is not implemented: many API routes use a hard-coded `TEMP_OWNER_ID` (see `backend/app/api/routes/*.py`). Don't change ownership checks without coordinating.

Developer workflows (concrete)
- Install backend deps (from repo root):
  - `cd backend && python -m pip install -r requirements.txt`
- Start backend (development):
  - `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
  - Health: `GET /api/health` → `http://localhost:8000/api/health`
- Create DB schema (requires `DATABASE_URL` in `.env`):
  - `cd backend && python create_tables.py`
- Quick DB smoke test (requires `.env`):
  - `cd backend && python test_db.py`
- Frontend dev:
  - `cd frontend && npm install && npm run dev` (Vite serves the UI; it expects backend at `/api` path).

Patterns and conventions
- Single FastAPI app with routers defined in `backend/app/api/routes/*.py` and aggregated in `backend/app/api/__init__.py`.
- DB session injected using dependency `get_db()` from `backend/app/core/db.py` (generator that yields a `Session` and closes it). Use `Depends(get_db)` in endpoints or functions.
- Models register themselves when imported (see `backend/create_tables.py`); to add tables, define models under `backend/app/models/models.py` and run the create script.
- Pipeline AST parsing uses `tree-sitter-python` and `tree-sitter-java` via `make_parser(lang)` in `languages.py`. Supported languages are `python` and `java`.
- Run lifecycle: `Run.status` and `Run.stage` are used to track processing; stages include `INGEST`, `TOKENS`, `FINGERPRINT`, `AST`, `AGGREGATE`, `REPORT`. Code that enqueues or processes runs will observe and update these fields.

Integration points & external deps
- Postgres database: set `DATABASE_URL` in `backend/.env` or environment. The app uses `psycopg2-binary`.
- Tree-sitter parsers: `tree-sitter-python` and `tree-sitter-java` are required (native extensions installed through pip packages listed in `backend/requirements.txt`).
- Frontend communicates to backend over REST at `/api/*`.

Editing guidance for AI agents
- Prefer small focused changes and run local dev commands above to validate (start backend, run create_tables, run frontend dev).
- When changing DB models: add SQLAlchemy model, run `create_tables.py` in a dev DB, and update any code that queries the model (search for `db.query(<ModelName>)`).
- When touching API routes: follow existing pattern: `router = APIRouter(prefix="/api/<resource>")`, use `Depends(get_db)`, return Pydantic schema models in `backend/app/schemas`.
- Do not assume auth — `TEMP_OWNER_ID` is used across routes; updating auth requires repository-wide changes.

References (examples)
- Backend entry: `backend/app/main.py`
- DB setup: `backend/app/core/db.py`
- Models: `backend/app/models/models.py`
- Create tables: `backend/create_tables.py`
- AST parsing: `backend/app/pipeline/ast/parser.py`, `languages.py`
- API routers: `backend/app/api/routes/*.py`
- Frontend: `frontend/package.json`, `frontend/README.md`

If anything is unclear or you want more detail (CI, migrations, or expected env values), tell me which area to expand and I will update this file.
