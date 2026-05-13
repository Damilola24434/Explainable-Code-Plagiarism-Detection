# Explainable Code Plagiarism Detection

Instructor-facing web platform for code plagiarism analysis with explainable output.

---

# System Overview

This system detects potential code plagiarism by analyzing uploaded source code files and generating explainable similarity reports.

The processing pipeline includes:

1. File ingestion
2. Token extraction
3. Abstract Syntax Tree (AST) analysis
4. Similarity scoring
5. Explainable report generation

The system supports asynchronous execution in two modes:

* **Docker Mode:** Uses Redis and Celery for queue-based asynchronous task processing.
* **Fallback Mode:** Uses background-thread asynchronous execution when Redis/Celery services are unavailable.

---

# Instructor Quick Start (Docker - Recommended)

## Prerequisites

* Docker Desktop installed and running
* Git installed
* A PostgreSQL connection string from the project team (`DATABASE_URL`)

---

## 1) Clone Repository

```bash
git clone https://github.com/Damilola24434/Explainable-Code-Plagiarism-Detection.git
cd Explainable-Code-Plagiarism-Detection
```

---

## 2) Create `.env` in project root

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST/DB?sslmode=require
```

---

## 3) Start Application

```bash
docker compose up --build -d
```

---

## 4) Open Application

* App UI: http://localhost:5173
* API health: http://127.0.0.1:8000/api/health
* API docs: http://127.0.0.1:8000/docs

---

## 5) Evaluation Workflow

1. Create a collection
2. Upload a ZIP of source files
3. Start an analysis run
4. Wait for completion
5. Inspect results
6. Export report PDF (optional)

---

## 6) Stop Application

```bash
docker compose down
```

---

# Instructor Quick Start (Without Docker – Fallback Mode)

If Docker cannot be started on your system, the application can be run manually.

This fallback mode still supports asynchronous execution using background-thread processing.

---

## Prerequisites

* Python 3.12+
* Node.js 18+
* PostgreSQL database (local or remote)
* Git

---

# Development Setup (Manual)

For developers who want to run components individually for development and testing.

---

# Backend Setup

## 1) Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

---

## 2) Create `.env` in `backend/`

```env
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST/DB
```

---

## 3) Create Database Tables

```bash
python create_tables.py
```

---

## 4) Test Database Connection (Optional)

```bash
python test_db.py
```

---

## 5) Start Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access:

* API Health: http://localhost:8000/api/health
* API Docs: http://localhost:8000/docs

---

# Frontend Setup

## 1) Install Node Dependencies

```bash
cd frontend
npm install
```

---

## 2) Start Frontend

```bash
npm run dev
```

Access:

* Frontend: http://localhost:5173
* API requests automatically proxy to backend

---

# Full Development Workflow

1. Start PostgreSQL database
2. Set up backend
3. Set up frontend
4. Open:

```text
http://localhost:5173
```

---

# Testing

Backend tests:

```bash
cd backend
python -m pytest
```

Frontend tests:

```bash
cd frontend
npm test
```

(if configured)

---

# What To Expect During Evaluation

Processing pipeline stages:

```text
INGEST -> TOKENS -> AST -> REPORT
```

Results include:

* Pairwise similarity scores
* Risk labels
* AST-based explainable spans
* Exportable similarity reports

---

# Verify Queue-Based Async Is Active (Docker Mode)

Queue-based asynchronous processing uses Redis + Celery.

To verify:

```bash
docker logs plagiarism-celery-worker --tail 100
```

Look for:

* `Task run_pipeline[...] received`
* `Task run_pipeline[...] succeeded`

---

# Troubleshooting

## App does not load

Ensure Docker Desktop is running, then:

```bash
docker compose up --build -d
```

---

## Collections fail with backend errors

Check:

* `.env` file
* `DATABASE_URL` value
* Database availability

---

## Check service status

```bash
docker ps
```

---

## Read backend logs

```bash
docker logs plagiarism-backend --tail 100
```

---

## Full restart

```bash
docker compose down
docker compose up --build -d
```

---

# Notes

* The repository intentionally excludes `.env` files and credentials.
* If credentials are missing, request the PostgreSQL connection string from the project team.
* The fallback execution mode allows operation without Redis/Celery services.
* This system is designed to support both containerized deployment and local development workflows.
