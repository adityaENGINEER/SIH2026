MILESTONE 9 — TUFFY AGENT ORCHESTRATOR

PROJECT:
SOVEREIGN AI WORKBENCH

CURRENT STATUS:

M1–M8 are completed and tested.

M1:
FastAPI foundation

M2:
Ollama + model registry

M3:
Real local Ollama inference

M4:
Document upload + local storage

M5:
Multi-format document extraction

M6:
Tesseract OCR

M7:
Local embeddings + NumPy vector store

M8:
Actual local RAG

Current embedding model:

nomic-embed-text

Embedding dimension:

768

Current general model:

qwen2.5:3b-instruct

Current vector store:

NumPyVectorStore

Current RAG:

RAGService

Current RAG endpoint:

POST /api/knowledge/query

--------------------------------------------------
M9 OBJECTIVE
--------------------------------------------------

Build the first version of:

TUFFY

Tuffy is the AGENT ORCHESTRATOR.

Tuffy is NOT an LLM.

Tuffy is NOT a chatbot.

Tuffy is the control/orchestration layer responsible for:

- receiving a task
- understanding task requirements
- creating a plan
- executing plan steps
- observing results
- validating progress
- deciding whether to continue
- deciding whether replanning is required
- completing the task
- exposing an auditable execution trace

Architecture:

                         USER TASK
                             │
                             ▼
                    ┌────────────────┐
                    │     TUFFY      │
                    │  ORCHESTRATOR  │
                    └───────┬────────┘
                            │
                            ▼
                         PLANNER
                            │
                            ▼
                          PLAN
                            │
                            ▼
                        EXECUTOR
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
              RAGService         Future Tools
              M8 existing         M10+
                 │                     │
                 ▼                     ▼
              RESULT                RESULT
                 │                     │
                 └──────────┬──────────┘
                            ▼
                         OBSERVE
                            │
                            ▼
                        VALIDATE
                            │
                     ┌──────┴──────┐
                     │             │
                   PASS           FAIL
                     │             │
                     ▼             ▼
                  NEXT STEP      REPLAN
                     │             │
                     └──────┬──────┘
                            ▼
                         COMPLETE

--------------------------------------------------
CRITICAL ARCHITECTURE RULE
--------------------------------------------------

Tuffy MUST be implemented as an orchestration/state-machine layer.

Do NOT implement Tuffy as:

"send the whole user prompt to qwen and ask it to act as an agent."

That is NOT acceptable.

The LLM may assist with planning where appropriate, but the actual state transitions, execution tracking, validation, and limits must be controlled by application code.

--------------------------------------------------
M9 SCOPE
--------------------------------------------------

M9 implements:

1. Tuffy state
2. Task lifecycle
3. Planner
4. Executor
5. Observation
6. Validation
7. Replanning
8. Execution trace
9. Task status
10. RAG capability integration
11. Safety limits
12. Agent API

M9 does NOT implement:

- Tool Registry
- File tools
- File writer
- Calculator tool
- Code execution
- Sandbox
- DOCX generation
- PPTX generation
- XLSX generation
- Vision
- Multimodal agents
- Model router redesign
- MongoDB
- authentication
- frontend
- Stitch

Those come later.

--------------------------------------------------
IMPORTANT M10 BOUNDARY
--------------------------------------------------

M10 will introduce:

Tool Registry
    ↓
Document Reader
File Reader
File Writer
Calculator
Knowledge Search
etc.

Therefore M9 MUST provide a clean capability interface.

Tuffy should not directly import random future tools.

For now, the ONLY real capability Tuffy may execute is:

RAG / Knowledge Query

using the existing:

RAGService

Do NOT create fake file tools.

Do NOT pretend sandbox execution works.

Do NOT return fabricated tool results.

--------------------------------------------------
TUFFY DIRECTORY
--------------------------------------------------

Create:

backend/app/agents/
    tuffy/
        __init__.py
        agent.py
        state.py
        planner.py
        executor.py
        observer.py
        validator.py
        replanner.py

If any equivalent files already exist:

REUSE THEM.

Do not duplicate architecture.

--------------------------------------------------
STATE MODEL
--------------------------------------------------

Create a strongly typed Tuffy state model.

Recommended fields:

task_id
user_request
status
current_step
plan
step_results
observations
validation_results
replan_count
max_replans
created_at
updated_at
final_result
error
execution_log

Use Pydantic models or dataclasses consistently with the existing backend architecture.

--------------------------------------------------
TASK STATUSES
--------------------------------------------------

Use explicit states:

queued
planning
executing
observing
validating
replanning
completed
failed
cancelled

Do not create dozens of unnecessary statuses.

--------------------------------------------------
PLAN MODEL
--------------------------------------------------

A plan consists of ordered steps.

Example:

{
  "plan_id": "...",
  "steps": [
    {
      "step_id": "step_1",
      "description": "Search the local knowledge base for inspection findings",
      "capability": "knowledge_search",
      "status": "pending"
    }
  ]
}

Each step should have:

step_id
description
capability
status
input
result
error

Statuses:

pending
running
completed
failed
skipped

--------------------------------------------------
PLANNER
--------------------------------------------------

Create:

backend/app/agents/tuffy/planner.py

The planner receives:

user_request

and determines the required plan.

IMPORTANT:

Do not blindly ask the LLM to generate arbitrary executable code.

The planner must produce a structured plan.

Use a constrained schema.

For example:

{
  "steps": [
    {
      "description": "...",
      "capability": "knowledge_search"
    }
  ]
}

Allowed M9 capability:

knowledge_search

Future capabilities:

document_reader
file_reader
file_writer
calculator
sandbox
document_generator

But these future capabilities must NOT execute in M9.

--------------------------------------------------
PLANNING STRATEGY
--------------------------------------------------

For M9 MVP, implement a hybrid strategy.

First:

1. Detect whether the task requires knowledge retrieval.

If yes:

create a knowledge_search step.

If task is unsupported:

return a clear unsupported-capability result.

Do NOT pretend arbitrary tasks can be executed.

This is preferable to a fake "fully autonomous" agent.

--------------------------------------------------
OPTIONAL LLM PLANNER
--------------------------------------------------

An LLM-assisted planner may be implemented only if it produces validated structured output.

If using qwen2.5:3b-instruct:

The model must output JSON matching the plan schema.

Application code MUST validate the JSON.

Never directly execute arbitrary model-generated commands.

If structured planning fails:

return PLANNING_FAILED.

Do not silently fall back to fabricated plans.

For M9 MVP, a deterministic planner is acceptable and preferred if it provides reliable behavior.

--------------------------------------------------
EXECUTOR
--------------------------------------------------

Create:

backend/app/agents/tuffy/executor.py

Executor responsibilities:

1. Receive validated plan.
2. Select the capability implementation.
3. Execute one step.
4. Capture result.
5. Capture error.
6. Return execution result.

For M9:

knowledge_search
    ↓
RAGService.query(...)

The executor must call the existing RAG service.

Do not duplicate RAG logic.

--------------------------------------------------
CAPABILITY INTERFACE
--------------------------------------------------

Create a small abstraction for future capabilities.

Conceptually:

Capability
    ├── name
    ├── description
    └── execute(input)

M9 implementation:

KnowledgeSearchCapability

Future M10:

FileReaderCapability
FileWriterCapability
CalculatorCapability
SandboxCapability
etc.

Do NOT build the M10 tools now.

--------------------------------------------------
KNOWLEDGE SEARCH CAPABILITY
--------------------------------------------------

Create an adapter around existing RAGService.

Conceptually:

Tuffy
 ↓
KnowledgeSearchCapability
 ↓
RAGService
 ↓
nomic-embed-text
 ↓
NumPy Vector Store
 ↓
qwen2.5:3b-instruct
 ↓
RAG result

Do not directly access vectors.npy.

Do not directly call Ollama from Tuffy.

Do not duplicate embedding logic.

--------------------------------------------------
OBSERVER
--------------------------------------------------

Create:

backend/app/agents/tuffy/observer.py

Observer records what happened after each execution step.

Observation should include:

step_id
status
result_summary
error
duration
timestamp

Do NOT log full sensitive document contents.

Do NOT log full LLM prompts.

Do NOT log full embeddings.

Safe metadata is sufficient.

--------------------------------------------------
VALIDATOR
--------------------------------------------------

Create:

backend/app/agents/tuffy/validator.py

Validator determines whether a step succeeded.

For knowledge_search:

PASS if:

- capability executed
- no execution error
- response is structurally valid
- result contains expected RAG fields

For example:

query
answer
grounded
sources
retrieval

FAIL if required structure is missing.

Do NOT claim semantic factual correctness just because the model returned text.

--------------------------------------------------
REPLANNER
--------------------------------------------------

Create:

backend/app/agents/tuffy/replanner.py

Replanning is required when a step fails and the task may still be recoverable.

Example:

Initial:

knowledge_search
    ↓
no relevant context

The re-planner may modify the retrieval strategy.

Example:

Plan:

knowledge_search(query="exact user query")

If no result:

replan:

knowledge_search(query=broader interpretation)

BUT:

Do not endlessly retry.

--------------------------------------------------
REPLAN LIMIT
--------------------------------------------------

Default:

max_replans = 2

Configuration:

TUFFY_MAX_REPLANS=2

If the maximum is reached:

status = failed

Return a clear reason.

No infinite agent loops.

--------------------------------------------------
EXECUTION LIMIT
--------------------------------------------------

Add:

TUFFY_MAX_STEPS=10

A task may not execute more than 10 steps.

This is a safety boundary.

--------------------------------------------------
TIMEOUT
--------------------------------------------------

Each capability execution should have a bounded timeout where appropriate.

Do not allow an agent task to run forever.

Reuse existing timeout configuration where possible.

Do not create arbitrary long-running loops.

--------------------------------------------------
TUFFY MAIN AGENT
--------------------------------------------------

Create:

backend/app/agents/tuffy/agent.py

Tuffy lifecycle:

1. Create task state.
2. Validate request.
3. Plan.
4. Validate plan.
5. Execute step.
6. Observe.
7. Validate.
8. If successful:
      continue
9. If failed:
      attempt replanning
10. If all steps complete:
      complete
11. If limits exceeded:
      fail safely

Conceptual loop:

PLAN
 ↓
EXECUTE
 ↓
OBSERVE
 ↓
VALIDATE
 ↓
 ┌───────────────┐
 │ Step valid?   │
 └───────┬───────┘
      YES│       NO
         │        │
         ▼        ▼
    NEXT STEP   REPLAN
         │        │
         │        ▼
         │     retry
         │        │
         └────────┘
              ↓
           COMPLETE

--------------------------------------------------
TASK STATE PERSISTENCE
--------------------------------------------------

Do NOT introduce MongoDB.

For M9 MVP use local filesystem.

Store Tuffy task state under:

D:\SovereignAI\storage\tasks\

Structure:

D:\SovereignAI\storage\tasks\
    <task_id>\
        state.json
        execution_log.json

This is temporary architecture.

Future database integration can replace the storage layer.

Do not store sensitive full prompts/results unnecessarily.

--------------------------------------------------
TASK API
--------------------------------------------------

Implement the planned task endpoints:

POST /api/tasks

GET /api/tasks/{task_id}

POST /api/tasks/{task_id}/run

GET /api/tasks/{task_id}/status

GET /api/tasks/{task_id}/result

GET /api/tasks/{task_id}/agent-log

Use existing API conventions.

--------------------------------------------------
CREATE TASK
--------------------------------------------------

POST:

/api/tasks

Request:

{
  "instruction": "Find the inspection findings for Pump P-101."
}

Response:

{
  "task_id": "...",
  "status": "queued"
}

Do not execute immediately unless architecture requires it.

--------------------------------------------------
RUN TASK
--------------------------------------------------

POST:

/api/tasks/{task_id}/run

This triggers Tuffy.

Response may indicate:

{
  "task_id": "...",
  "status": "processing"
}

For MVP, synchronous execution is acceptable if it remains bounded.

If asynchronous execution is already supported by the backend architecture, reuse it.

Do not introduce a heavy queue system in M9.

--------------------------------------------------
STATUS API
--------------------------------------------------

GET:

/api/tasks/{task_id}/status

Return:

{
  "task_id": "...",
  "status": "executing",
  "current_step": "step_1",
  "progress": {
      "completed_steps": 0,
      "total_steps": 1
  }
}

Do not fake progress.

Progress must reflect actual execution state.

--------------------------------------------------
RESULT API
--------------------------------------------------

GET:

/api/tasks/{task_id}/result

Return the actual final Tuffy result.

For a knowledge task:

{
  "task_id": "...",
  "status": "completed",
  "result": {
      "answer": "...",
      "grounded": true,
      "sources": [...]
  }
}

Do not generate fake results.

--------------------------------------------------
AGENT LOG
--------------------------------------------------

GET:

/api/tasks/{task_id}/agent-log

Return structured execution events.

Example:

[
  {
    "timestamp": "...",
    "event": "task_created"
  },
  {
    "timestamp": "...",
    "event": "planning_started"
  },
  {
    "timestamp": "...",
    "event": "plan_created",
    "step_count": 1
  },
  {
    "timestamp": "...",
    "event": "step_started",
    "step_id": "step_1"
  },
  {
    "timestamp": "...",
    "event": "step_completed",
    "step_id": "step_1"
  },
  {
    "timestamp": "...",
    "event": "validation_passed",
    "step_id": "step_1"
  },
  {
    "timestamp": "...",
    "event": "task_completed"
  }
]

Do not expose sensitive document content.

--------------------------------------------------
ERROR HANDLING
--------------------------------------------------

Reuse existing error format:

{
  "error": {
    "code": "...",
    "message": "..."
  }
}

Possible errors:

TASK_NOT_FOUND
TASK_FAILED
PLANNING_FAILED
INVALID_PLAN
EXECUTION_FAILED
VALIDATION_FAILED
REPLAN_LIMIT_REACHED
STEP_LIMIT_REACHED
CAPABILITY_NOT_FOUND
RAG_FAILED
OLLAMA_UNAVAILABLE
OLLAMA_TIMEOUT

Do not expose stack traces.

--------------------------------------------------
UNSUPPORTED TASKS
--------------------------------------------------

Example:

User:

"Create a PowerPoint presentation from this document."

M9 currently does NOT have a document-generation capability.

Tuffy must respond:

"Document generation capability is not available yet."

It must NOT:

- pretend PPTX was created
- call arbitrary shell commands
- fabricate a file
- claim completion

This capability will be added later.

--------------------------------------------------
EXAMPLE SUPPORTED TASK
--------------------------------------------------

User:

"Find the inspection findings for Pump P-101."

Tuffy:

PLAN
 ↓
knowledge_search
 ↓
RAGService
 ↓
retrieval
 ↓
grounded answer
 ↓
validation
 ↓
complete

Expected result:

{
  "answer": "...",
  "grounded": true,
  "sources": [...]
}

--------------------------------------------------
EXAMPLE MULTI-STEP TASK
--------------------------------------------------

M9 may support a simple multi-step knowledge plan such as:

Step 1:
Search for Pump P-101 inspection findings.

Step 2:
Search for the recommended action related to the same finding.

Step 3:
Combine the retrieved results.

BUT:

Only use capabilities that actually exist.

Do not create fake second capabilities.

If implementing this, use multiple calls to the existing RAGService.

--------------------------------------------------
RAG INTEGRATION
--------------------------------------------------

Tuffy must treat RAG as a capability.

Do not rewrite:

RAGService
EmbeddingService
VectorStore

Use them as existing services.

--------------------------------------------------
LOCAL-ONLY
--------------------------------------------------

Tuffy must remain local.

Allowed:

FastAPI
local filesystem
RAGService
localhost Ollama

Forbidden:

cloud APIs
OpenAI
Gemini
external agents
external task queues

--------------------------------------------------
SECURITY
--------------------------------------------------

The LLM must never be allowed to directly execute:

PowerShell
CMD
Python
shell commands
arbitrary files

M10/M13 will introduce controlled tools and sandboxing.

M9 must NOT execute arbitrary model-generated commands.

This is critical.

--------------------------------------------------
AGENT LOGGING
--------------------------------------------------

Log:

task_id
step_id
event
status
duration
capability name
error code

Do not log:

full user documents
full retrieved context
full model prompt
full model response
embedding vectors

--------------------------------------------------
CONFIGURATION
--------------------------------------------------

Add through existing config:

TUFFY_MAX_STEPS=10
TUFFY_MAX_REPLANS=2

Reuse existing config.py.

Do not duplicate configuration loading.

--------------------------------------------------
TESTING
--------------------------------------------------

Create:

backend/test_m9.py

Tests MUST include:

1. Tuffy initialization
2. task creation
3. task persistence
4. deterministic planning
5. plan schema validation
6. knowledge_search capability
7. RAG integration
8. real local RAG execution
9. observation recording
10. validation
11. task completion
12. task status
13. task result
14. agent log
15. unsupported capability handling
16. step limit
17. replan limit
18. failed execution handling
19. nonexistent task handling
20. local-only execution
21. M1–M8 regression
22. real qwen2.5:3b-instruct inference

--------------------------------------------------
MANDATORY REAL TUFFY TEST
--------------------------------------------------

Do NOT fake agent execution.

Use an actually indexed document.

Example:

Document:

"Inspection found excessive vibration in Pump P-101."

Create task:

"Find the inspection problem identified for Pump P-101."

Execute:

POST /api/tasks
 ↓
POST /api/tasks/{id}/run
 ↓
Tuffy planning
 ↓
knowledge_search
 ↓
RAG
 ↓
validation
 ↓
completed

Verify actual answer.

--------------------------------------------------
REPLAN TEST
--------------------------------------------------

Create a task that initially produces no useful result.

Verify:

initial execution
 ↓
validation failure
 ↓
replanner
 ↓
retry
 ↓
either success or controlled failure

Verify replan count never exceeds:

TUFFY_MAX_REPLANS

Do NOT fake a successful replan.

--------------------------------------------------
UNSUPPORTED TASK TEST
--------------------------------------------------

Task:

"Create a PowerPoint from the inspection report."

Expected:

capability unavailable / controlled failure.

Must NOT create a fake PPT.

--------------------------------------------------
STEP LIMIT TEST
--------------------------------------------------

Force/test a plan that exceeds:

TUFFY_MAX_STEPS

Expected:

STEP_LIMIT_REACHED

No infinite execution.

--------------------------------------------------
PERSISTENCE TEST
--------------------------------------------------

Create task.

Run task.

Stop backend.

Restart backend.

Retrieve:

GET /api/tasks/{task_id}

Verify state remains available.

--------------------------------------------------
REGRESSION
--------------------------------------------------

Verify all previous APIs:

GET /api/health

GET /api/system/status

GET /api/models

POST /api/models/generate

POST /api/documents/upload

GET /api/documents/{document_id}

GET /api/documents/{document_id}/download

GET /api/documents/{document_id}/content

POST /api/ocr/process

GET /api/ocr/{ocr_id}

POST /api/knowledge/index

POST /api/knowledge/search

POST /api/knowledge/query

All must remain working.

--------------------------------------------------
PERFORMANCE
--------------------------------------------------

Machine:

AMD Ryzen 5 5500U
~7.5 GB RAM
Integrated Radeon graphics

Do not preload multiple LLMs.

Tuffy should not maintain multiple Ollama models in memory.

Use:

nomic-embed-text
for embeddings

qwen2.5:3b-instruct
for generation

Sequential operation is acceptable.

--------------------------------------------------
ARCHITECTURE
--------------------------------------------------

Expected:

backend/
└── app/
    ├── agents/
    │   └── tuffy/
    │       ├── __init__.py
    │       ├── agent.py
    │       ├── state.py
    │       ├── planner.py
    │       ├── executor.py
    │       ├── observer.py
    │       ├── validator.py
    │       └── replanner.py
    │
    ├── services/
    │   └── ...
    │
    └── api/
        └── routes/
            └── tasks.py

If equivalent files already exist:

REUSE THEM.

--------------------------------------------------
FUTURE M10
--------------------------------------------------

M10 will introduce:

TOOL REGISTRY + LOCAL TOOLS

Expected:

Tuffy
 ↓
Tool Registry
 ↓
Tool
 ↓
Result
 ↓
Tuffy

Tools will include:

- document_reader
- file_reader
- file_writer
- calculator
- knowledge_search
- document_generator
- sandbox_executor

M9 should therefore keep capability/tool execution abstract.

--------------------------------------------------
NO UI
--------------------------------------------------

DO NOT create:

React
CSS
Stitch UI
dashboard
frontend components

Backend only.

--------------------------------------------------
TESTING DISCIPLINE
--------------------------------------------------

Follow:

EXPLAIN
↓
IMPLEMENT
↓
TEST
↓
VERIFY
↓
REPORT
↓
STOP

Before implementation:

1. Inspect M8 RAGService.
2. Inspect knowledge routes.
3. Inspect config.py.
4. Inspect existing storage service.
5. Inspect existing error handling.
6. Inspect document deletion behavior.
7. Inspect existing task-related files if any.

Then implement.

Do not rewrite working M1–M8 code.

Do not modify unrelated files.

Do not claim PASS without real execution.

--------------------------------------------------
FINAL REPORT
--------------------------------------------------

When complete report:

1. Implementation status
2. Files created
3. Files modified
4. Dependencies added
5. Tuffy architecture
6. State model
7. Planner behavior
8. Executor behavior
9. Observer behavior
10. Validator behavior
11. Replanner behavior
12. Capability architecture
13. RAG integration
14. Task APIs
15. Persistence
16. Agent log
17. Real Tuffy execution test
18. Replanning test
19. Unsupported task test
20. Step limit test
21. Local-only verification
22. M1–M8 regression
23. Real Ollama inference
24. Limitations
25. Exact backend run command
26. Exact test command

Then:

STOP.

DO NOT START M10.