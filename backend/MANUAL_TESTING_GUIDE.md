# Manual Testing Guide — M16 Builder AI Workbench

## 1. Prerequisites
- **Python:** 3.10+
- **Ollama:** Installed and running locally
- **Tesseract OCR:** Installed and added to system PATH
- **Docker:** Optional (used for sandbox when available)

## 2. Python Environment Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 3. Storage Setup
Ensure the following directory structure exists (or allow the app to create it):
```
D:\SovereignAI\storage
```

## 4. Environment Variables
Create a `.env` file in the `backend` directory:
```
OLLAMA_BASE_URL=http://localhost:11434
STORAGE_ROOT=D:\SovereignAI\storage
CORS_ORIGINS=["http://localhost:3000"]
```

## 5. Ollama Models
Ensure you have pulled the required models.
```powershell
ollama pull qwen2.5:3b-instruct
ollama pull nomic-embed-text
```

## 6. Start Backend
```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

## 7. Open API Docs
Open your browser to:
[http://localhost:8000/docs](http://localhost:8000/docs)

## 8. Testing Endpoints

### 8.1 Health Test
```powershell
curl -X GET "http://localhost:8000/api/health"
```
*Expected: `{"status": "ok", "service": "builder-ai-workbench"}`*

### 8.2 Project Test
```powershell
curl -X POST "http://localhost:8000/api/projects" -H "Content-Type: application/json" -d "{\"name\":\"My Test Project\",\"description\":\"Testing M16\",\"project_type\":\"standard\"}"
```
*Take note of the `project_id`.*

### 8.3 Agent Run History
```powershell
curl -X GET "http://localhost:8000/api/projects/<project_id>/agent-runs"
```

### 8.4 Security Dashboard APIs
```powershell
curl -X GET "http://localhost:8000/api/security/summary"
curl -X GET "http://localhost:8000/api/security/events"
curl -X GET "http://localhost:8000/api/projects/<project_id>/security/events"
```

## 9. Deliverable Generation and Approvals
Refer to the Swagger UI (`/docs`) to test the `POST /api/projects/{project_id}/approvals` endpoint for creating reviews, and `GET /api/projects/{project_id}/deliverables/{deliverable_id}/download` for downloading artifacts (DOCX, PDF, PPTX, XLSX).


client id :- nitm0nbbeoY6GPitqRkX3z
client secret :- UAYpAqoZMGUPDmPShrwTR5mVc31xy6MbsHn592Bi