import os
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

project_id = f"proj_{datetime.now().strftime('%Y%m%d')}_{os.urandom(4).hex()}"

def test_create_project():
    global project_id
    res = httpx.post(f"{BASE_URL}/projects", json={
        "name": "Stage 5 Test Project",
        "description": "Agent run and security test",
        "project_type": "standard"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    project_id = data["project_id"]
    print("Project created:", project_id)

def test_agent_run_history():
    # Since we need an agent run, let's create a task manually using Tuffy
    res = httpx.post(f"{BASE_URL}/tasks", json={
        "user_request": "Test task",
        "project_id": project_id
    })
    assert res.status_code == 200, res.text
    data = res.json()
    task_id = data["task_id"]
    print("Created dummy task:", task_id)
    
    # Check agent-runs endpoint
    res = httpx.get(f"{BASE_URL}/projects/{project_id}/agent-runs")
    assert res.status_code == 200, res.text
    runs = res.json()
    assert isinstance(runs, list)
    assert len(runs) >= 1
    assert runs[0]["task_id"] == task_id
    print("Agent run history ok")
    
    # Check single agent run
    res = httpx.get(f"{BASE_URL}/projects/{project_id}/agent-runs/{task_id}")
    assert res.status_code == 200, res.text
    run = res.json()
    assert run["task_id"] == task_id
    print("Single agent run ok")

def test_security_telemetry():
    # Get summary
    res = httpx.get(f"{BASE_URL}/security/summary")
    assert res.status_code == 200, res.text
    summary = res.json()
    assert "total_evaluations" in summary
    assert "outbound_calls" in summary
    print("Security summary ok")
    
    # Get events
    res = httpx.get(f"{BASE_URL}/security/events")
    assert res.status_code == 200, res.text
    events = res.json()
    assert isinstance(events, list)
    print("Security events ok")
    
    # Get project events
    res = httpx.get(f"{BASE_URL}/projects/{project_id}/security/events")
    assert res.status_code == 200, res.text
    events = res.json()
    assert isinstance(events, list)
    print("Project security events ok")

if __name__ == "__main__":
    print("--- M16 STAGE 5 TESTS ---")
    test_create_project()
    test_agent_run_history()
    test_security_telemetry()
    print("All Stage 5 tests passed!")
