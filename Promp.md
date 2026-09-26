M14 — VISION + MULTIMODAL INTELLIGENCE

Project: SOVEREIGN AI WORKBENCH

M1-M13 are COMPLETE and VERIFIED.

IMPORTANT:
Do NOT rebuild the project.
Do NOT modify working M1-M13 behavior unnecessarily.
Do NOT create frontend/UI.
Do NOT add database.
Do NOT redesign Tuffy.
Do NOT start M15.

GOAL:

Add local multimodal/vision capability so Tuffy can analyze:

- images
- inspection photographs
- scanned PDF pages
- engineering drawings/images

using a LOCAL Ollama vision model.

Everything must remain local.
No cloud vision APIs.
No external image upload.

==================================================
1. INSPECT EXISTING ARCHITECTURE FIRST
==================================================

Inspect:

- ollama_service.py
- model_registry.py
- model_router.py
- document_extractor.py
- ocr_service.py
- rag_service.py
- tuffy/planner.py
- tuffy/agent.py
- tuffy/validator.py
- ToolRegistry
- existing document APIs
- existing configuration

Reuse existing architecture.

==================================================
2. VISION MODEL
==================================================

Add configurable vision model support.

Preferred model:

qwen2.5vl:3b

Do NOT automatically download/pull models.

If model is not installed:
return a clear:

MODEL_NOT_INSTALLED

error.

Do NOT fake vision results.

Keep existing:

qwen2.5:3b-instruct
nomic-embed-text

unchanged.

==================================================
3. OLLAMA VISION SERVICE
==================================================

Extend the existing Ollama service with a vision generation method.

Conceptually:

image
  ↓
Ollama vision model
  ↓
text description / structured analysis

Support:

- prompt
- image input
- model selection
- timeout
- local-only execution

Do not send images anywhere outside localhost Ollama.

==================================================
4. IMAGE PROCESSING
==================================================

Create a controlled image/vision service.

Suggested:

backend/app/services/vision_service.py

It should:

- validate image type
- validate file existence
- validate file size
- normalize supported image formats if required
- send image to local Ollama vision model
- return structured result
- handle missing model
- handle Ollama unavailable
- handle timeout

Initially support:

PNG
JPG/JPEG
WEBP

Do not add unnecessary formats.

==================================================
5. API
==================================================

Add:

POST /api/vision/analyze

Input:

- image
- prompt

Return structured response similar to:

{
  "vision_id": "...",
  "status": "completed",
  "model": "qwen2.5vl:3b",
  "analysis": "...",
  "local": true
}

Also provide:

GET /api/vision/{vision_id}

for retrieving the stored result/status.

Do NOT expose arbitrary filesystem paths.

==================================================
6. SCANNED PDF INTEGRATION
==================================================

Reuse the existing OCR pipeline.

Current architecture:

PDF
 ↓
document extraction
 ↓
if text exists → normal extraction
if no text → OCR

Extend only where necessary:

Scanned PDF
     ↓
page image
     ↓
OCR
     ↓
optional Vision analysis
     ↓
normalized document information

Do NOT replace existing OCR.

Do NOT make vision mandatory for every PDF.

Vision should be used when:

- document is scanned
- image content is important
- user explicitly requests visual analysis

==================================================
7. IMAGE TOOL
==================================================

Add a ToolRegistry tool:

analyze_image

The tool should follow the existing ToolBase interface.

Tuffy should be able to call:

ToolRegistry
   ↓
analyze_image
   ↓
VisionService
   ↓
Ollama vision model

No direct filesystem access outside approved storage.

==================================================
8. TUFFY INTEGRATION
==================================================

Extend planner heuristics for requests such as:

- analyze this image
- analyze inspection photo
- inspect this photograph
- analyze this drawing
- analyze P&ID image
- understand this scanned document
- identify visible equipment
- inspect this scanned page
- use Approtiate model according to user task

Example plan:

USER
 ↓
TUFFY
 ↓
VISION ANALYSIS
 ↓
OBSERVE
 ↓
VALIDATE
 ↓
RESULT

For a multimodal approval task:

DOCUMENT
 ↓
OCR
 ↓
VISION
 ↓
RAG
 ↓
Tuffy
 ↓
Approval Document

Do NOT break existing text-only approval workflows.

==================================================
9. STRUCTURED VISION OUTPUT
==================================================

Where possible, ask the vision model to return structured information.

Example:

{
  "description": "...",
  "objects": [],
  "observations": [],
  "visible_text": [],
  "warnings": [],
  "uncertainties": []
}

Do NOT force fields that the image does not support.

If something cannot be determined:

"Not determinable from image."

Do NOT hallucinate equipment IDs, measurements, names, dates or safety conditions.

==================================================
10. SAFETY / LIMITATIONS

Vision output must be treated as AI analysis, not authoritative inspection certification.

For industrial/safety images:

include:

"AI-generated visual analysis. Human verification required."

Do not claim that an image proves equipment is safe.

==================================================
11. LOCAL-ONLY REQUIREMENT

Verify that vision calls only use:

http://localhost:11434

No:

- OpenAI API
- Gemini API
- cloud vision
- external image services
- external upload endpoints

No network dependency should be introduced.

==================================================
12. TESTS

Create:

backend/test_m14.py

Test:

TEST 1
Vision service exists.

TEST 2
Image validation.

TEST 3
Unsupported file rejection.

TEST 4
Missing image handling.

TEST 5
Vision model availability handling.

TEST 6
Real local vision inference using qwen2.5vl:3b IF installed.

If model is not installed, test must report
MODEL_NOT_INSTALLED rather than pretending success.

TEST 7
Vision API.

TEST 8
Vision result retrieval.

TEST 9
ToolRegistry contains analyze_image.

TEST 10
Tuffy recognizes image-analysis intent.

TEST 11
Tuffy executes vision capability.

TEST 12
Scanned-document/OCR compatibility.

TEST 13
Existing M1-M13 regression tests.

IMPORTANT:
Do NOT mock successful vision inference and call it a real test.

==================================================
13. HARDWARE AWARENESS

The machine has approximately:

Ryzen 5 5500U
~7.5 GB RAM
integrated AMD graphics
no dedicated GPU

Therefore:

- use qwen2.5vl:3b
- do not require large vision models
- process one image at a time
- use strict timeouts
- avoid loading multiple large models simultaneously

Do NOT redesign model routing yet.

==================================================
14. ERROR HANDLING

Use existing error contract.

Relevant errors:

MODEL_NOT_INSTALLED
OLLAMA_UNAVAILABLE
OLLAMA_TIMEOUT
INVALID_FILE_TYPE
FILE_NOT_FOUND
VISION_FAILED

Do not invent a second error format.

==================================================
15. REGRESSION

Run:

python test_m14.py

Then:

python test_m13.py
python test_m12.py
python test_m11.py
python test_m10.py
python test_m9.py

Also run the complete available backend test suite if practical.

Do not claim success unless tests actually pass.

==================================================
16. MILESTONE DISCIPLINE

Follow:

INSPECT
↓
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

At the end report:

1. Files created
2. Files modified
3. Vision model used (As according to the user task)
4. Whether real local inference was tested
5. API endpoints
6. Tuffy integration
7. Security/local-only verification
8. test_m14.py result
9. M1-M13 regression result
10. Any limitations

STOP AFTER M14.

DO NOT START M15.