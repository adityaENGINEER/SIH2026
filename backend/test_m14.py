import os
import json
import base64
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.tools.registry import tool_registry
from app.services.vision_service import vision_service
from app.services.ollama_service import ollama_service

client = TestClient(app)

def create_dummy_image(path):
    # create a valid 1x1 png file
    img_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(img_data)

def test_1_vision_service_exists():
    assert vision_service is not None
    assert callable(vision_service.analyze)

def test_2_image_validation():
    img_path = os.path.join(settings.storage_root, "test_img.png")
    create_dummy_image(img_path)
    assert vision_service.validate_image(img_path) == True
    os.remove(img_path)

def test_3_unsupported_file_rejection():
    file_path = os.path.join(settings.storage_root, "test_doc.docx")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write("test")
    try:
        vision_service.validate_image(file_path)
        assert False
    except ValueError as e:
        assert "INVALID_FILE_TYPE" in str(e)
    os.remove(file_path)

def test_4_missing_image_handling():
    try:
        vision_service.validate_image("/non/existent/path.png")
        assert False
    except ValueError as e:
        assert "FILE_NOT_FOUND" in str(e)

import asyncio
def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

def test_5_and_6_vision_inference():
    img_path = os.path.join(settings.storage_root, "test_vision.png")
    create_dummy_image(img_path)
    
    # Check if model installed
    installed = run_async(ollama_service.is_model_installed(settings.vision_model))
    
    res = run_async(vision_service.analyze(img_path, prompt="What is this?"))
    if not installed:
        assert "error" in res
        assert res["error"]["code"] == "MODEL_NOT_INSTALLED"
    else:
        assert res["status"] == "completed"
        assert "analysis" in res
        assert "safety_warning" in res["analysis"] or "Human verification required" in res["analysis"]
    os.remove(img_path)

def test_7_vision_api():
    img_path = os.path.join(settings.storage_root, "test_api.png")
    create_dummy_image(img_path)
    
    res = client.post("/api/vision/analyze", json={"file_path": img_path, "prompt": "test"})
    
    installed = run_async(ollama_service.is_model_installed(settings.vision_model))
    if not installed:
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "MODEL_NOT_INSTALLED"
    else:
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert "vision_id" in data
        
        # TEST 8 retrieval
        vid = data["vision_id"]
        res2 = client.get(f"/api/vision/{vid}")
        assert res2.status_code == 200
        assert res2.json()["vision_id"] == vid
        
    os.remove(img_path)

def test_9_tool_registry():
    tools = tool_registry.list_tools()
    assert any(t["name"] == "analyze_image" for t in tools)

def test_10_tuffy_recognizes_intent():
    res = client.post("/api/tasks", json={"user_request": "analyze this image"})
    task_id = res.json()["task_id"]
    from app.agents.tuffy.agent import agent
    state = agent.get_state(task_id)
    # The planner only runs during execution, so let's trigger plan
    from app.agents.tuffy.planner import planner
    plan = planner.create_plan(state)
    assert len(plan.steps) > 0
    assert any(s.input.get("tool_name") == "analyze_image" for s in plan.steps)

def test_11_tuffy_executes_vision():
    # To test execution without a real image or model, we just ensure it correctly errors out or succeeds
    img_path = os.path.join(settings.storage_root, "test_tuffy.png")
    create_dummy_image(img_path)
    
    # Upload image first
    with open(img_path, "rb") as f:
        upload_res = client.post("/api/documents/upload", files={"file": ("test_tuffy.png", f, "image/png")})
    
    doc_id = upload_res.json()["document_id"]
    
    # Create task
    task_res = client.post("/api/tasks", json={"user_request": "analyze this image", "document_id": doc_id})
    task_id = task_res.json()["task_id"]
    
    run_res = client.post(f"/api/tasks/{task_id}/run", timeout=20.0)
    data = run_res.json()
    
    installed = run_async(ollama_service.is_model_installed(settings.vision_model))
    if not installed:
        assert data["status"] == "failed"
    else:
        assert data["status"] == "completed"
    
    os.remove(img_path)

def test_12_scanned_document_ocr():
    # If a scanned document is requested for vision, it is passed via file_path to vision service
    # Vision service now supports pdf by rendering the first page
    pdf_path = os.path.join(settings.storage_root, "test_tuffy.pdf")
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50,50), "Test PDF")
        doc.save(pdf_path)
        doc.close()
    except Exception:
        # Fallback if fitz not installed
        with open(pdf_path, "w") as f:
            f.write("dummy")
            
    with open(pdf_path, "rb") as f:
        upload_res = client.post("/api/documents/upload", files={"file": ("test_tuffy.pdf", f, "application/pdf")})
        
    doc_id = upload_res.json()["document_id"]
    
    task_res = client.post("/api/tasks", json={"user_request": "analyze this scanned document", "document_id": doc_id})
    task_id = task_res.json()["task_id"]
    
    run_res = client.post(f"/api/tasks/{task_id}/run", timeout=20.0)
    data = run_res.json()
    
    installed = run_async(ollama_service.is_model_installed(settings.vision_model))
    print("M14 Test 12 RUN DATA:", data)
    if not installed:
        assert data["status"] == "failed"
    else:
        assert data["status"] == "completed"
        
    try:
        os.remove(pdf_path)
    except:
        pass

def test_13_regression():
    res = client.get("/api/health")
    assert res.status_code == 200

if __name__ == "__main__":
    test_1_vision_service_exists()
    test_2_image_validation()
    test_3_unsupported_file_rejection()
    test_4_missing_image_handling()
    test_5_and_6_vision_inference()
    test_7_vision_api()
    test_9_tool_registry()
    test_10_tuffy_recognizes_intent()
    test_11_tuffy_executes_vision()
    test_12_scanned_document_ocr()
    test_13_regression()
    print("ALL M14 TESTS PASSED")
