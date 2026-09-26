# Sovereign AI Workbench (Builder AI)

Local, offline-first industrial AI workbench: document-grounded report generation,
an autonomous agent orchestrator ("Tuffy"), project-scoped RAG, vision/OCR for
scanned documents, a sandboxed tool runner, and a human approval/sign-off loop.

## SIH Problem Statement

Industrial teams need AI assistance over their own project documents without
sending sensitive data to third-party clouds. This project provides a fully
local workbench: upload project documents, ask questions grounded in those
documents with verbatim evidence, generate DOCX/PPTX deliverables, and run
multi-step agent tasks — all against a host-local Ollama runtime, with human
approval required before high-impact actions execute.

## Architecture

```text
Frontend (React + Vite, :5173)
   │  REST /api/*
   ▼
Backend (FastAPI, :8000)
   ├── Tuffy agent  (Planner → Executor → Observer → Validator → Replanner)
   ├── RAG service  (NumPy vector store, project-scoped retrieval)
   ├── Vision / OCR (Moondream via Ollama, Tesseract fallback)
   ├── Sandbox tool runner + approval / sign-off lifecycle
   └── Document deliverables (DOCX/PPTX grounded in retrieved evidence)
   │  Ollama client (:11434)
   ▼
Host Ollama (development / supported AI runtime)
```

`docker-compose.yml` additionally defines `ollama` + `model-provisioner`
services, but **Ollama Docker provisioning is currently NOT validated**
(see Known Limitations). The supported runtime path is **host Ollama**.

## Tech Stack

| Layer    | Technology                                                  |
|----------|-------------------------------------------------------------|
| Frontend | React 19, React Router 8, Vite 8, TailwindCSS 4, TypeScript |
| Backend  | Python 3.12, FastAPI, Uvicorn, Pydantic / pydantic-settings |
| AI       | Ollama (host), NumPy vector store, PyMuPDF, Tesseract OCR   |
| Docs     | python-docx, openpyxl, reportlab, python-pptx, Pillow        |
| Deploy   | Docker + Docker Compose (backend/frontend images validated) |

## Main Features

- **Projects & documents** — upload PDFs/DOCX/XLSX/images per project; text
  extraction plus OCR for scanned pages.
- **ChatBench** — project-scoped chat grounded in retrieved chunks with
  verbatim evidence citations.
- **Tuffy agent runs** — autonomous multi-step tasks with live run timeline,
  terminal-state polling, and recovery of orphaned runs on server restart.
- **Approvals & sign-off** — high-impact tool calls pause for human approval;
  runs complete only after sign-off.
- **Tools & sandbox** — tool registry with sandboxed execution and audit trail.
- **Models & security** — model registry/router status, project isolation,
  security overview pages; all wired to real backend endpoints (no mock data).

## Tuffy Agent Workflow

1. **Planner** — decomposes the goal into steps with stable step IDs and
   declared dependencies.
2. **Executor** — runs steps (RAG queries, document ops, tool calls) in order.
3. **Observer** — records observations per step.
4. **Validator** — checks step outputs; failures trigger error recovery.
5. **Replanner** — on failure, replans while preserving stable step IDs so the
   UI timeline stays consistent.
6. Orphaned (non-terminal) runs from a previous server process are recovered
   to a terminal state on startup.

## RAG / Vision / Sandbox / Approval Workflow

- **RAG** — documents are chunked, embedded (`nomic-embed-text`), and stored in
  a NumPy vector store. Retrieval is masked by `allowed_document_ids`, so a
  project can only ever see its own documents. Retrieved chunks are passed
  verbatim as evidence into the deterministic document generator.
- **Vision** — image/scanned-PDF pages route to `moondream` via Ollama, with
  Tesseract OCR as fallback; extracted text re-enters the normal chunk/index
  pipeline.
- **Sandbox** — tool calls execute in a sandboxed runner; every invocation is
  logged and auditable.
- **Approval** — tool calls flagged high-impact create an approval request;
  execution pauses until a human approves/rejects, and the run requires final
  sign-off.

## Prerequisites

- Python 3.12, Node 22+, Docker Desktop (optional, backend/frontend only).
- **Host Ollama** installed and serving on `http://localhost:11434`:

```powershell
ollama serve
ollama pull qwen2.5:3b-instruct
ollama pull moondream:latest
ollama pull nomic-embed-text:latest
```

Required models:

| Model                | Used for                        |
|----------------------|---------------------------------|
| `qwen2.5:3b-instruct`| Text reasoning / document analysis |
| `moondream:latest`   | Vision on images / scanned PDFs |
| `nomic-embed-text:latest` | Embeddings for the vector store |

> **Note:** `docker-compose.yml` contains `ollama` and `model-provisioner`
> services (`scripts/provision-models.sh` pulls the same three tags), but the
> Ollama-in-Docker path is **currently not validated** — the large
> `ollama/ollama:latest` layer fails to commit in this environment
> (containerd snapshot-store corruption, orphaned snapshot). **Use host Ollama
> as the development/runtime path.** Do not treat full Docker/Ollama
> deployment as working.

## Environment Variables / Setup

```powershell
# Backend
Copy-Item backend\.env.example backend\.env
# Frontend
Copy-Item Frontend\.env.example Frontend\.env  # if present, else set VITE_API_URL
```

Root `.env.example` documents both sides. Key variables:

| Variable          | Default                              | Meaning                              |
|-------------------|--------------------------------------|--------------------------------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434`             | Host Ollama endpoint                 |
| `GENERAL_MODEL`   | `qwen2.5:3b-instruct`                | Text model                           |
| `VISION_MODEL`    | `moondream`                          | Vision model                         |
| `EMBEDDING_MODEL` | `nomic-embed-text`                   | Embedding model                      |
| `STORAGE_ROOT`    | `D:\SovereignAI\storage`             | Local document/run storage           |
| `MAX_UPLOAD_SIZE_MB` | `50`                              | Upload cap                           |
| `CORS_ORIGINS`    | `http://localhost:5173,...`          | Allowed browser origins              |
| `VITE_API_URL`    | `http://localhost:8000`              | Backend URL baked into frontend build|

Never commit real `.env` files — they are git-ignored.

## Run (Host Dev)

```powershell
# Backend (:8000)
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (:5173)
cd Frontend
npm ci
npm run dev
```

Health: `GET http://localhost:8000/api/health`.

## Run (Docker — Backend/Frontend Only)

Backend and frontend images build successfully; Compose file is valid:

```powershell
# Build + run backend & frontend (requires host Ollama or running ollama service)
docker compose build backend frontend
docker compose up backend frontend
```

- Backend: `http://localhost:8000` (`STORAGE_ROOT=/data/storage` in container).
- Frontend (nginx): `http://localhost:5173` (`VITE_API_URL` build arg, default
  `http://localhost:8000`).
- `docker compose up --build` (full stack incl. Ollama) is **not validated** —
  see Known Limitations.

## Known Limitations

1. **Ollama Docker provisioning NOT validated.** `docker compose pull ollama`
   fails committing the ~3.6 GB `ollama/ollama:latest` layer in this
   environment (`unexpected commit digest ... failed precondition`, orphaned
   containerd snapshot `snapshots/126/fs: no such file or directory`). No code
   or Compose changes are made for this; host Ollama is the supported path.
2. Full `docker compose up --build` (three-service) deployment is therefore
   **not claimed working**. Backend + frontend container builds are validated.
3. Vision quality depends on the local `moondream` model; OCR fallback is
   Tesseract (bundled in backend image).
4. Storage is local filesystem (`STORAGE_ROOT` / `sovereign-storage` volume);
   no multi-user auth or cloud backup is provided.
