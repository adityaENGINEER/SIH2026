import os
import time
import requests
import asyncio
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# ================================
# TOOL TESTS
# ================================

def test_tool_registry_discovery():
    response = client.get("/api/tools")
    assert response.status_code == 200
    tools = response.json()
    names = [t["name"] for t in tools]
    assert "calculator" in names
    assert "file_reader" in names
    assert "file_writer" in names
    assert "document_reader" in names

def test_calculator_tool_valid():
    response = client.post("/api/tools/calculator/execute", json={"expression": "100 * 0.18"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["result"]["value"] == 18.0

def test_calculator_tool_complex():
    response = client.post("/api/tools/calculator/execute", json={"expression": "(25 + 15) / 2"})
    assert response.status_code == 200
    assert response.json()["result"]["value"] == 20.0

def test_calculator_tool_injection():
    response = client.post("/api/tools/calculator/execute", json={"expression": "import os; os.system('ls')"})
    assert response.status_code == 200
    assert response.json()["status"] == "failed"

def test_file_writer_and_reader():
    test_path = "storage/temp/test_m10.txt"
    content = "Hello M10 tool test!"
    
    # Write
    write_res = client.post("/api/tools/file_writer/execute", json={"path": test_path, "content": content})
    assert write_res.status_code == 200
    assert write_res.json()["status"] == "completed"
    
    # Read
    read_res = client.post("/api/tools/file_reader/execute", json={"path": test_path})
    assert read_res.status_code == 200
    assert read_res.json()["status"] == "completed"
    assert read_res.json()["result"]["content"] == content

def test_file_writer_path_traversal():
    traversal_path = "../../../windows/win.ini"
    res = client.post("/api/tools/file_writer/execute", json={"path": traversal_path, "content": "hack"})
    assert res.status_code == 200
    assert res.json()["status"] == "failed"
    assert "PATH_NOT_ALLOWED" in res.json()["error"]["message"]

def test_tool_not_found():
    res = client.post("/api/tools/hacker_tool/execute", json={})
    assert res.status_code == 200
    assert res.json()["status"] == "failed"
    assert res.json()["error"]["code"] == "TOOL_NOT_FOUND"

# ================================
# DOCUMENT + TASK TESTS
# ================================

def create_text_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def upload_file(path):
    with open(path, "rb") as f:
        res = client.post("/api/documents/upload", files={"file": f})
    assert res.status_code == 200
    return res.json()

def test_document_indexing_integration():
    file_path = "test_doc_m10_1.txt"
    create_text_file(file_path, "Inspection found excessive vibration in Pump P-101.")
    
    upload_res = upload_file(file_path)
    doc_id = upload_res["document_id"]
    
    assert upload_res["storage_status"] == "stored"
    assert upload_res["content_status"] == "extracted"
    assert upload_res["index_status"] == "indexed"
    
    # Create task
    task_req = {
        "user_request": "What problem was found in Pump P-101?",
        "document_id": doc_id
    }
    task_res = client.post("/api/tasks", json=task_req)
    assert task_res.status_code == 200
    task_id = task_res.json()["task_id"]
    
    # Run task (Agent executes KnowledgeSearchCapability)
    run_res = client.post(f"/api/tasks/{task_id}/run")
    assert run_res.status_code == 200
    run_data = run_res.json()
    
    assert run_data["status"] == "completed"
    
    # Verify result mentions P-101 and vibration
    ans = run_data["result"]["answer"].lower()
    assert "p-101" in ans
    assert "vibration" in ans
    
    os.remove(file_path)

def test_document_isolation():
    file_a = "test_doc_a.txt"
    file_b = "test_doc_b.txt"
    create_text_file(file_a, "Pump P-101 had excessive vibration.")
    create_text_file(file_b, "Pump P-202 had a temperature issue.")
    
    doc_a = upload_file(file_a)["document_id"]
    doc_b = upload_file(file_b)["document_id"]
    
    # Task scoped to Doc A
    task_a = client.post("/api/tasks", json={
        "user_request": "What problem was found?",
        "document_id": doc_a
    }).json()["task_id"]
    
    run_a = client.post(f"/api/tasks/{task_a}/run").json()
    ans_a = run_a["result"]["answer"].lower()
    assert "p-101" in ans_a or "vibration" in ans_a
    assert "p-202" not in ans_a
    assert "temperature" not in ans_a
    
    os.remove(file_a)
    os.remove(file_b)

if __name__ == "__main__":
    print("--- REGRESSION TESTS ---")
    response = client.get("/api/health")
    print("Health:", response.json())
    
    print("\n--- M10 TESTS (TOOLS & INDEXING) ---")
    
    print("Running Tools tests...")
    test_tool_registry_discovery()
    test_calculator_tool_valid()
    test_calculator_tool_complex()
    test_calculator_tool_injection()
    test_file_writer_and_reader()
    test_file_writer_path_traversal()
    test_tool_not_found()
    print("Tools tests PASSED")
    
    print("Running Document Indexing Pipeline tests (Will take a moment for LLM)...")
    test_document_indexing_integration()
    print("Document Indexing Pipeline test PASSED")
    
    print("Running Document Isolation tests (Will take a moment for LLM)...")
    test_document_isolation()
    print("Document Isolation test PASSED")
    
    print("\nAll M10 tests completed successfully.")
