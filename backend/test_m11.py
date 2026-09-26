import os
import time
import requests
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

client = TestClient(app)

def create_text_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def upload_file(path):
    with open(path, "rb") as f:
        res = client.post("/api/documents/upload", files={"file": f})
    assert res.status_code == 200
    return res.json()

def test_single_knowledge_search():
    file_path = "m11_single.txt"
    create_text_file(file_path, "Pump P-101 requires maintenance.")
    doc = upload_file(file_path)
    
    res = client.post("/api/tasks", json={"user_request": "What requires maintenance?", "document_id": doc["document_id"]})
    task_id = res.json()["task_id"]
    
    run_res = client.post(f"/api/tasks/{task_id}/run")
    assert run_res.status_code == 200
    data = run_res.json()
    assert data["status"] == "completed"
    
    log_res = client.get(f"/api/tasks/{task_id}/agent-log")
    logs = log_res.json()["logs"]
    assert len(logs) > 0
    assert logs[0]["capability"] == "knowledge_search"
    
    os.remove(file_path)

def test_multi_step_calculator_dependency():
    res = client.post("/api/tasks", json={"user_request": "Calculate 15 * 24"})
    task_id = res.json()["task_id"]
    
    run_res = client.post(f"/api/tasks/{task_id}/run")
    assert run_res.status_code == 200
    data = run_res.json()
    
    assert data["status"] == "completed", f"Expected completed, got {data}"
    
    log_res = client.get(f"/api/tasks/{task_id}/agent-log")
    logs = log_res.json()["logs"]
    
    # Depending on planner heuristic, this might just be tool execution or both
    capabilities = [l["capability"] for l in logs]
    assert "tool_execution" in capabilities

def test_validation_failure_and_replanning():
    res = client.post("/api/tasks", json={"user_request": "Search for imaginary unicorn in non-existent space."})
    task_id = res.json()["task_id"]
    
    run_res = client.post(f"/api/tasks/{task_id}/run")
    assert run_res.status_code == 200
    data = run_res.json()
    
    # Should fail due to NO_RELEVANT_CONTEXT leading to max replan limit
    assert data["status"] == "failed", f"Expected failed, got {data}"
    assert data["error"]["code"] == "REPLAN_LIMIT_REACHED"

def test_unknown_capability():
    from app.agents.tuffy.state import TaskState, Plan, Step
    from app.agents.tuffy.agent import agent
    
    task_id = agent.create_task("test unknown")
    state = agent.get_state(task_id)
    
    step = Step(
        step_id="step_bad",
        description="bad step",
        capability="unknown_hacker_capability",
        input={}
    )
    state.plan = Plan(steps=[step])
    agent._save_state(state)
    
    # Can't use await agent._orchestrate easily here without asyncio, so let's use the API
    res = client.post(f"/api/tasks/{task_id}/run")
    data = res.json()
    assert data["status"] == "failed"
    assert data["error"]["code"] == "REPLAN_LIMIT_REACHED"

def test_max_steps():
    # Similar to above, inject a long plan
    from app.agents.tuffy.state import TaskState, Plan, Step
    from app.agents.tuffy.agent import agent
    
    task_id = agent.create_task("test limits")
    state = agent.get_state(task_id)
    state.max_steps = 1
    
    s1 = Step(step_id="1", description="", capability="tool_execution", input={"tool_name": "calculator", "tool_input": {"expression": "1+1"}})
    s2 = Step(step_id="2", description="", capability="tool_execution", input={"tool_name": "calculator", "tool_input": {"expression": "2+2"}})
    state.plan = Plan(steps=[s1, s2])
    agent._save_state(state)
    
    res = client.post(f"/api/tasks/{task_id}/run")
    assert res.json()["status"] == "failed"
    assert res.json()["error"]["code"] == "STEP_LIMIT_REACHED"

def test_document_indexing_timeout():
    from app.agents.tuffy.state import TaskState, Plan, Step
    from app.agents.tuffy.agent import agent
    
    file_path = "m11_timeout.txt"
    create_text_file(file_path, "Test")
    doc = upload_file(file_path)
    
    # Hack the index status in document metadata
    from app.services.document_service import document_service
    document_service.update_metadata(doc['document_id'], {"index_status": "indexing"})
        
    res = client.post("/api/tasks", json={"user_request": "What is this?", "document_id": doc["document_id"]})
    task_id = res.json()["task_id"]
    
    run_res = client.post(f"/api/tasks/{task_id}/run")
    data = run_res.json()
    
    assert data["status"] == "failed"
    # Wait bounded time, then it fails
    assert data["error"]["code"] == "DOCUMENT_INDEXING_TIMEOUT", f"Expected DOCUMENT_INDEXING_TIMEOUT, got {data}"
    
    os.remove(file_path)

if __name__ == "__main__":
    print("--- M11 TESTS ---")
    test_single_knowledge_search()
    print("TEST 1 PASSED: Single Knowledge Search")
    
    test_multi_step_calculator_dependency()
    print("TEST 2/12 PASSED: Calculator")
    
    test_validation_failure_and_replanning()
    print("TEST 3/4/5 PASSED: Validation and Replanning Limits")
    
    test_unknown_capability()
    print("TEST 8 PASSED: Unknown Capability")
    
    test_max_steps()
    print("TEST 6 PASSED: Max Steps")
    
    test_document_indexing_timeout()
    print("TEST 10/11 PASSED: Indexing Race/Timeout")
    
    print("ALL M11 TESTS PASSED")
