import httpx
import time

BASE_URL = "http://localhost:8000/api"
project_id = None

def test_create_project():
    global project_id
    res = httpx.post(f"{BASE_URL}/projects", json={
        "name": "Project Alpha",
        "description": "Test project",
        "project_type": "industrial"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "project_id" in data
    assert data["name"] == "Project Alpha"
    project_id = data["project_id"]
    print(f"Project created: {project_id}")

def test_list_projects():
    res = httpx.get(f"{BASE_URL}/projects")
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert any(p["project_id"] == project_id for p in data)
    print("List projects ok")

def test_get_project():
    res = httpx.get(f"{BASE_URL}/projects/{project_id}")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["project_id"] == project_id
    assert data["name"] == "Project Alpha"
    print("Get project ok")

def test_update_project():
    res = httpx.patch(f"{BASE_URL}/projects/{project_id}", json={
        "name": "Project Alpha Updated"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["name"] == "Project Alpha Updated"
    print("Update project ok")

def test_create_conversation():
    global conversation_id
    res = httpx.post(f"{BASE_URL}/projects/{project_id}/conversations", json={
        "title": "My first chat"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "conversation_id" in data
    conversation_id = data["conversation_id"]
    print(f"Conversation created: {conversation_id}")

def test_chat_simple():
    res = httpx.post(f"{BASE_URL}/projects/{project_id}/conversations/{conversation_id}/messages", json={
        "message": "Hello AI",
        "mode": "chat"
    }, timeout=30.0)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["role"] == "assistant"
    assert data["execution_mode"] == "chat"
    print("Simple chat ok")

def test_chat_agent():
    res = httpx.post(f"{BASE_URL}/projects/{project_id}/conversations/{conversation_id}/messages", json={
        "message": "Calculate 2+2",
        "mode": "agent"
    }, timeout=30.0)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["role"] == "assistant"
    assert data["execution_mode"] == "agent"
    assert "task_id" in data
    print("Agent chat initiation ok")

def test_chat_history():
    res = httpx.get(f"{BASE_URL}/projects/{project_id}/chat/history")
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    print("Chat history ok")

import os

def test_document_upload_project():
    global document_id
    with open("test_m16_doc.txt", "w") as f:
        f.write("This is a test document for M16 project scoping. It contains industrial safety protocols.")
        
    with open("test_m16_doc.txt", "rb") as f:
        res = httpx.post(f"{BASE_URL}/documents/upload", files={"file": ("test_m16_doc.txt", f, "text/plain")}, data={"project_id": project_id}, timeout=30.0)
    
    assert res.status_code == 200, res.text
    data = res.json()
    assert "document_id" in data
    document_id = data["document_id"]
    print(f"Document uploaded with project_id: {document_id}")
    
    os.remove("test_m16_doc.txt")

def test_get_project_documents():
    res = httpx.get(f"{BASE_URL}/projects/{project_id}/documents")
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert any(d["document_id"] == document_id for d in data)
    print("Get project documents ok")

def test_get_document_sources():
    # Might need to wait for indexing to finish
    time.sleep(2)
    res = httpx.get(f"{BASE_URL}/projects/{project_id}/documents/{document_id}/sources")
    assert res.status_code == 200, res.text
    data = res.json()
    assert "sources" in data
    assert isinstance(data["sources"], list)
    if len(data["sources"]) > 0:
        assert "chunk_id" in data["sources"][0]
        assert "text" in data["sources"][0]
    print(f"Get document sources ok. Found {len(data['sources'])} sources.")

if __name__ == "__main__":
    print("--- M16 STAGE 1 TESTS ---")
    test_create_project()
    test_list_projects()
    test_get_project()
    test_update_project()
    print("All Stage 1 tests passed!")
    
    print("--- M16 STAGE 2 TESTS ---")
    test_create_conversation()
    test_chat_simple()
    test_chat_agent()
    test_chat_history()
    print("All Stage 2 tests passed!")

    print("--- M16 STAGE 3 TESTS ---")
    test_document_upload_project()
    test_get_project_documents()
    test_get_document_sources()
    print("All Stage 3 tests passed!")
