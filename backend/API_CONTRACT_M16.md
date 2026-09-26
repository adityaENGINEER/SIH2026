# API Contract — M16 Builder AI Workbench Backend

> **Version**: M16 (Stages 1–4)  
> **Base URL**: `http://localhost:8000/api`  
> **Architecture**: Local-only, no external APIs, no database, no cloud.  
> **Storage**: `D:\SovereignAI\storage\`

---

## Table of Contents

1. [Projects API (Stage 1)](#1-projects-api)
2. [Conversations & Chat API (Stage 2)](#2-conversations--chat-api)
3. [Document Library & Sources API (Stage 3)](#3-document-library--sources-api)
4. [Approvals API (Stage 4)](#4-approvals-api)
5. [Deliverables API (Stage 4)](#5-deliverables-api)
6. [State Machines](#6-state-machines)
7. [Error Codes](#7-error-codes)
8. [Project Isolation](#8-project-isolation)

---

## 1. Projects API

Storage: `D:\SovereignAI\storage\projects\{project_id}\project.json`

### Create Project
```
POST /api/projects
```
**Body:**
```json
{
  "name": "string",
  "description": "string",
  "project_type": "string"
}
```
**Response:** `ProjectResponse`

### List Projects
```
GET /api/projects
```
**Response:** `ProjectResponse[]`

### Get Project
```
GET /api/projects/{project_id}
```
**Response:** `ProjectResponse`

### Update Project
```
PATCH /api/projects/{project_id}
```
**Body:** partial `ProjectResponse` fields  
**Response:** updated `ProjectResponse`

### Delete Project
```
DELETE /api/projects/{project_id}
```
**Response:** `{ "status": "ok" }`

### ProjectResponse Schema
```json
{
  "project_id": "proj_20260925_abc123",
  "name": "string",
  "description": "string",
  "project_type": "string",
  "created_at": "2026-09-25T12:00:00Z",
  "updated_at": "2026-09-25T12:00:00Z"
}
```

---

## 2. Conversations & Chat API

Storage: `D:\SovereignAI\storage\projects\{project_id}\conversations\{conversation_id}.json`

### Create Conversation
```
POST /api/projects/{project_id}/conversations
```
**Body:**
```json
{ "title": "string" }
```
**Response:** `ConversationResponse`

### List Conversations
```
GET /api/projects/{project_id}/conversations
```
**Response:** `ConversationResponse[]`

### Get Conversation
```
GET /api/projects/{project_id}/conversations/{conversation_id}
```
**Response:** `ConversationResponse`

### Delete Conversation
```
DELETE /api/projects/{project_id}/conversations/{conversation_id}
```

### Send Message
```
POST /api/projects/{project_id}/conversations/{conversation_id}/messages
```
**Body:**
```json
{
  "message": "string",
  "mode": "chat | agent | auto",
  "document_ids": ["doc_abc123"]
}
```
**Modes:**
- `chat` → Direct Ollama generation
- `agent` → Tuffy agent task creation (returns `task_id`)
- `auto` → Heuristic routing (defaults to `agent`)

**Response:** `MessageResponse`

### Get Chat History
```
GET /api/projects/{project_id}/chat/history
GET /api/projects/{project_id}/chat/history?date=2026-09-25
```

### MessageResponse Schema
```json
{
  "message_id": "msg_abc123",
  "conversation_id": "conv_abc123",
  "project_id": "proj_abc123",
  "role": "user | assistant",
  "content": "string",
  "execution_mode": "chat | agent | null",
  "task_id": "task_abc123 | null",
  "status": "completed | running | failed",
  "created_at": "2026-09-25T12:00:00Z"
}
```

---

## 3. Document Library & Sources API

Storage: `D:\SovereignAI\storage\uploads\{document_id}\`

### Upload Document (with optional project_id)
```
POST /api/documents/upload
Content-Type: multipart/form-data
```
**Form fields:**
- `file` (required): the document file
- `project_id` (optional): associates this document with a project

**Supported formats:** `.pdf`, `.docx`, `.txt`, `.xlsx`, `.csv`, `.png`, `.jpg`, `.jpeg`  
**Max size:** 50 MB

**Response:**
```json
{
  "document_id": "doc_20260925_abc123",
  "filename": "report.pdf",
  "content_type": "application/pdf",
  "size_bytes": 12345,
  "status": "uploaded",
  "storage_status": "stored",
  "content_status": "pending | extracted",
  "index_status": "not_indexed | indexed | requires_ocr"
}
```

### List Documents for Project
```
GET /api/projects/{project_id}/documents
```
Returns only documents uploaded with the matching `project_id`.  
**Response:** `DocumentMetadata[]`

**Project isolation:** A project ID never returns documents from another project.

### Get Document Metadata
```
GET /api/documents/{document_id}
```

### Download Document
```
GET /api/documents/{document_id}/download
```

### Delete Document
```
DELETE /api/documents/{document_id}
```

### Get Document Content
```
GET /api/documents/{document_id}/content
```

### Get Document Sources (Chunk Explainability)
```
GET /api/documents/{document_id}/sources
```
Returns chunk-level metadata from the **NumPy vector store** (in-memory `metadata` list).  
**No FAISS is used.** Sources only exist for indexed documents.

**Response:**
```json
{
  "document_id": "doc_20260925_abc123",
  "sources": [
    {
      "document_id": "doc_20260925_abc123",
      "chunk_id": "doc_20260925_abc123_chunk_0001",
      "text": "The extracted chunk text...",
      "source": {
        "filename": "report.pdf",
        "page": 1,
        "type": "pdf"
      }
    }
  ]
}
```

---

## 4. Approvals API

Storage: `D:\SovereignAI\storage\reviews\{project_id}\{approval_id}.json`

### Create Approval
```
POST /api/projects/{project_id}/approvals
```
**Body:**
```json
{
  "title": "string",
  "conversation_id": "string | null",
  "task_id": "string | null",
  "agent_run_id": "string | null",
  "deliverable_id": "string | null",
  "source_document_ids": ["doc_abc"],
  "output_document_ids": ["doc_xyz"]
}
```
Initial status is always `DRAFT`.  
**AI/Tuffy NEVER creates an approval in APPROVED status.**

**Response:** `ApprovalResponse`

### List Approvals
```
GET /api/projects/{project_id}/approvals
```
**Response:** `ApprovalResponse[]`

### Get Approval
```
GET /api/projects/{project_id}/approvals/{approval_id}
```
**Response:** `ApprovalResponse`  
**404** if not found or belongs to a different project.

### Submit for Human Review (DRAFT → PENDING_HUMAN_SIGNOFF)
```
POST /api/projects/{project_id}/approvals/{approval_id}/submit
```
No body required. Transitions `DRAFT → PENDING_HUMAN_SIGNOFF`.  
**400** if already submitted or in a terminal state.

### Approve (Human Action Only)
```
POST /api/projects/{project_id}/approvals/{approval_id}/approve
```
**Body:**
```json
{
  "approver_name": "Jane Smith",
  "employee_id": "EMP-1234",
  "reason": "All conditions met.",
  "comment": "Reviewed and approved after inspection."
}
```
Transitions `PENDING_HUMAN_SIGNOFF → APPROVED`.  
Persists: `approver_name`, `employee_id`, `approval_reason`, `review_comment`, `reviewed_at`, `signature_status: "signed"`.

**400** if not in `PENDING_HUMAN_SIGNOFF` state.

### Reject (Human Action Only)
```
POST /api/projects/{project_id}/approvals/{approval_id}/reject
```
**Body:**
```json
{
  "approver_name": "Inspector X",
  "employee_id": "EMP-007",
  "reason": "Non-compliant conditions.",
  "comment": "Return for correction."
}
```
Transitions `PENDING_HUMAN_SIGNOFF → REJECTED`.  
Persists: `approver_name`, `employee_id`, `rejection_reason`, `review_comment`, `reviewed_at`.

**400** if not in `PENDING_HUMAN_SIGNOFF` state.

### ApprovalResponse Schema
```json
{
  "approval_id": "appr_abc123def456",
  "project_id": "proj_20260925_abc123",
  "conversation_id": null,
  "task_id": "task_abc123",
  "agent_run_id": null,
  "deliverable_id": "dlvr_abc123",
  "title": "Safety Inspection Authorization",
  "status": "DRAFT | PENDING_HUMAN_SIGNOFF | APPROVED | REJECTED",
  "created_at": "2026-09-25T12:00:00Z",
  "updated_at": "2026-09-25T12:05:00Z",
  "submitted_at": "2026-09-25T12:03:00Z",
  "reviewed_at": "2026-09-25T12:10:00Z",
  "approver_name": "Jane Smith",
  "employee_id": "EMP-1234",
  "review_comment": "Approved after inspection.",
  "rejection_reason": null,
  "approval_reason": "All checks passed.",
  "signature_status": "unsigned | signed",
  "source_document_ids": ["doc_abc"],
  "output_document_ids": ["doc_xyz"]
}
```

---

## 5. Deliverables API

Storage: `D:\SovereignAI\storage\outputs\{project_id}\{deliverable_id}\`

### Generate Deliverable
```
POST /api/projects/{project_id}/deliverables
```
**Body:**
```json
{
  "project_id": "proj_abc123",
  "title": "Safety Report",
  "format": "DOCX | PDF | PPTX | XLSX",
  "content": "Full text content for the deliverable body.",
  "task_id": "task_abc | null",
  "approval_id": "appr_abc | null"
}
```
**Supported formats:**
| Format | Library | Notes |
|--------|---------|-------|
| DOCX | python-docx | Reuses M12 generator patterns |
| PDF | ReportLab | PDF magic bytes verified |
| PPTX | python-pptx | Multi-slide deck |
| XLSX | openpyxl | Structured spreadsheet |

File is **physically generated and verified to exist** before responding.  
**400** for unsupported formats. No fake successful responses.

**Response:** `DeliverableResponse`

### List Deliverables
```
GET /api/projects/{project_id}/deliverables
```
**Response:** `DeliverableResponse[]`

### Get Deliverable Metadata
```
GET /api/projects/{project_id}/deliverables/{deliverable_id}
```
**Response:** `DeliverableResponse`  
**404** if not found or belongs to a different project.

### Download Deliverable
```
GET /api/projects/{project_id}/deliverables/{deliverable_id}/download
```
**Response:** Binary file stream (`application/octet-stream`)  
**404** if not found or file missing from disk.  
**Path traversal is blocked** at both storage and download layers.

### DeliverableResponse Schema
```json
{
  "deliverable_id": "dlvr_abc123def456",
  "project_id": "proj_20260925_abc123",
  "task_id": "task_abc123",
  "approval_id": "appr_abc123",
  "type": "DOCX | PDF | PPTX | XLSX",
  "filename": "Safety_Report.docx",
  "path": "D:\\SovereignAI\\storage\\outputs\\proj_abc\\dlvr_abc\\Safety_Report.docx",
  "created_at": "2026-09-25T12:00:00Z",
  "size": 36790,
  "status": "ready"
}
```

---

## 6. State Machines

### Approval Lifecycle

```
                     [AI creates approval]
                            |
                         DRAFT
                            |
               submit (system/AI action)
                            |
                 PENDING_HUMAN_SIGNOFF
                      /          \
          approve (human)    reject (human)
               /                    \
          APPROVED               REJECTED
        (terminal)              (terminal)
```

**Strict enforcement — invalid transitions return 400:**

| From | To | Result |
|------|----|--------|
| DRAFT | APPROVED | ❌ 400 INVALID_APPROVAL_STATE |
| DRAFT | REJECTED | ❌ 400 INVALID_APPROVAL_STATE |
| APPROVED | REJECTED | ❌ 400 INVALID_APPROVAL_STATE |
| REJECTED | APPROVED | ❌ 400 INVALID_APPROVAL_STATE |
| PENDING_HUMAN_SIGNOFF | APPROVED | ✅ requires human payload |
| PENDING_HUMAN_SIGNOFF | REJECTED | ✅ requires human payload |

### Workflow Integration
```
Task / Tuffy Agent
       |
  Generated Output
       |
   Deliverable  (POST /api/projects/{pid}/deliverables)
       |
   Approval     (POST /api/projects/{pid}/approvals, deliverable_id linked)
       |
   Submit       (POST .../submit)   ← AI/system may trigger
       |
 PENDING_HUMAN_SIGNOFF
       |
 Human Review   (POST .../approve | .../reject)  ← HUMAN ONLY
       |
APPROVED / REJECTED
```

---

## 7. Error Codes

All errors follow the format:
```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable description."
  }
}
```

| Code | HTTP | Description |
|------|------|-------------|
| `PROJECT_NOT_FOUND` | 404 | Project does not exist |
| `CONVERSATION_NOT_FOUND` | 404 | Conversation does not exist |
| `APPROVAL_NOT_FOUND` | 404 | Approval not found or belongs to different project |
| `DELIVERABLE_NOT_FOUND` | 404 | Deliverable not found or belongs to different project |
| `DELIVERABLE_FILE_MISSING` | 404 | Metadata exists but file missing from disk |
| `INVALID_APPROVAL_STATE` | 400 | State transition not allowed |
| `APPROVAL_ALREADY_FINAL` | 400 | Approval is in a terminal state (APPROVED/REJECTED) |
| `APPROVAL_PROJECT_MISMATCH` | 400 | Approval belongs to a different project |
| `UNSUPPORTED_FORMAT` | 400 | Deliverable format not in DOCX/PDF/PPTX/XLSX |
| `DELIVERABLE_GENERATION_FAILED` | 400 | File generation error |
| `DELIVERABLE_ACCESS_DENIED` | 400 | Path traversal detected |
| `DOCUMENT_NOT_FOUND` | 404 | Document metadata not found |
| `INVALID_FILE_TYPE` | 400 | Unsupported or unsafe file extension |
| `FILE_TOO_LARGE` | 400 | File exceeds 50 MB limit |
| `EMBEDDING_MODEL_UNAVAILABLE` | 400 | Embedding model not loaded in Ollama |

---

## 8. Project Isolation

All project-scoped resources enforce strict isolation at the service layer:

- **Approvals**: stored under `reviews/{project_id}/`. `get_approval()` checks that `data["project_id"] == project_id`.
- **Deliverables**: stored under `outputs/{project_id}/`. `get_deliverable()` checks that `meta["project_id"] == project_id`.
- **Documents**: `GET /api/projects/{project_id}/documents` scans uploads and filters by `metadata["project_id"]`.
- **Conversations**: stored under `projects/{project_id}/conversations/`.

**A resource belonging to Project A is never accessible via Project B's routes. All cross-project attempts return 404.**

Path traversal is blocked at every write and read with `os.path.abspath()` prefix checks.

---

## Architecture Notes

- **No database**: all persistence is JSON files on `D:\SovereignAI\storage\`.
- **No FAISS**: vector store is `NumPyVectorStore` using `.npy` + `metadata.json`.
- **No external APIs**: all inference via local Ollama (`http://localhost:11434`).
- **No authentication**: all endpoints are open (M17 scope).
- **No frontend modifications**: this contract is for backend consumption by the frontend.

---

## 9. Tasks & Agent Runs

### Agent Run History (Project-Scoped)
```http
GET /api/projects/{project_id}/agent-runs
```
**Response:** `TaskState[]`

### Single Agent Run (Project-Scoped)
```http
GET /api/projects/{project_id}/agent-runs/{run_id}
```
**Response:** `TaskState`

### Get Task Log
```http
GET /api/tasks/{task_id}/agent-log
```
**Response:** `{ "task_id": "...", "logs": [ Observation ] }`

---

## 10. Security & Sovereign Telemetry

### Security Summary
```http
GET /api/security/summary
```
**Response:**
```json
{
  "total_evaluations": 0,
  "outbound_calls": 0,
  "blocked_calls": 0,
  "local_calls": 0
}
```

### Global Security Events
```http
GET /api/security/events
```
**Response:** `Event[]`

### Project-Scoped Security Events
```http
GET /api/projects/{project_id}/security/events
```
**Response:** `Event[]`

---

## 11. Integration Phase Additions

### Project-Scoped Documents
```http
GET    /api/projects/{project_id}/documents/{document_id}
GET    /api/projects/{project_id}/documents/{document_id}/download
GET    /api/projects/{project_id}/documents/{document_id}/sources
DELETE /api/projects/{project_id}/documents/{document_id}
```
404 `DOCUMENT_NOT_FOUND` unless the document belongs to `project_id`.
The legacy `/api/documents/{document_id}[/download|/content|/sources]` and `DELETE /api/documents/{document_id}`
now return 404 for project-owned documents; they only serve documents that belong to no project.
`POST /api/documents/upload` returns 404 `PROJECT_NOT_FOUND` for an unknown `project_id`.

### Global Task Routes
`/api/tasks/{task_id}*` return `TASK_NOT_FOUND` for project-owned runs; use the project agent-run routes.

### Knowledge Scope
`POST /api/knowledge/search` and `/api/knowledge/query` accept an optional `project_id`.
Scope: `document_id` → that document only (must belong to `project_id`, else `DOCUMENT_NOT_IN_PROJECT`);
`project_id` → that project's documents; neither → only documents that belong to no project.
RAG responses include `evidence`: `[{document_id, filename, page_number, chunk_id, text}]`, bounded by `rag_max_context_chars`.

### Agent Run Cancellation
```http
POST /api/projects/{project_id}/agent-runs/{run_id}/cancel
```
**Response:** `TaskState`. Sets `cancel_requested`. A run without a live worker becomes `cancelled` immediately;
a running run stops before its next step (an in-flight Ollama call is allowed to finish, its result is kept) and ends `cancelled`.

### TaskState additions
`cancel_requested`, `routing` (`{model, purpose, reason, capability}`), `completed_at`, `deliverable_id`, `approval_id`.
Non-terminal runs with no worker in the current process (e.g. after a backend restart) are marked
`failed` with error code `ORPHANED_RUN` at startup and whenever they are read.

### Chat Message additions
`MessageResponse.routing` — the model router decision made by the backend for the request.
`MessageResponse.error` — set with `status: "failed"` when chat inference fails.

### Approval Deliverables from Tuffy
A completed Tuffy run that generates an approval DOCX registers it as a project deliverable, creates an approval
record (`DRAFT`) and submits it for review (`PENDING_HUMAN_SIGNOFF`). Only the human approve/reject endpoints can
set `APPROVED` / `REJECTED`.

### Security
```http
GET /api/security/summary?project_id={project_id}
GET /api/projects/{project_id}/security/summary
```
`GET /api/security/events` returns only system-level events (no `project_id`); project events are only available
through the project route. Every Ollama generate/vision/embedding call is logged as `model_call`; a non-local
Ollama endpoint is blocked and logged as `network_attempt` (`blocked: true`). Tool executions log `tool_execution`.
