import httpx
import time

BASE_URL = "http://localhost:8000/api"

def print_test(name, result):
    print(f"{name}: {result}")

def run_tests():
    print("--- REGRESSION TESTS ---")
    try:
        r = httpx.get(f"{BASE_URL}/health")
        print_test("Health", r.json())
    except Exception as e:
        print_test("Health Failed", str(e))
        return

    print("\n--- M9 TESTS (TUFFY ORCHESTRATOR) ---")
    
    # 1. Create a document in knowledge base to search
    try:
        files = {'file': ('doc_m9.txt', b'Inspection found excessive vibration in Pump P-101.', 'text/plain')}
        doc_id = httpx.post(f"{BASE_URL}/documents/upload", files=files).json().get("document_id")
        httpx.get(f"{BASE_URL}/documents/{doc_id}/content")
        httpx.post(f"{BASE_URL}/knowledge/index", json={"document_id": doc_id}, timeout=120)
        print_test("Indexed Document for M9", doc_id)
    except Exception as e:
        print_test("Document Upload/Index Failed", str(e))
        return
        
    # 2. Test 1: Real integration (Normal Flow)
    try:
        print("\nTest 1: Normal execution flow (Pump inspection)")
        # Create Task
        r = httpx.post(f"{BASE_URL}/tasks", json={"user_request": "Find the inspection problem identified for Pump P-101."})
        task_id = r.json().get("task_id")
        print_test("Task Created", task_id)
        
        # Run Task
        print("Running Tuffy agent...")
        r = httpx.post(f"{BASE_URL}/tasks/{task_id}/run", timeout=180)
        res = r.json()
        print_test("Task Finished Status", res.get("status"))
        print_test("Task Final Result", res.get("result", {}).get("answer"))
        
        # Check logs
        r_log = httpx.get(f"{BASE_URL}/tasks/{task_id}/agent-log")
        print_test("Observations Count", len(r_log.json().get("logs", [])))
    except Exception as e:
        print_test("Test 1 Failed", str(e))

    # 3. Test 2: Replanning (Hallucination/No-context fallback)
    try:
        print("\nTest 2: Replanning execution flow (Unknown manufacturing cost)")
        # Create Task
        r = httpx.post(f"{BASE_URL}/tasks", json={"user_request": "Find the manufacturing cost of a component that does not exist in the knowledge base."})
        task_id2 = r.json().get("task_id")
        print_test("Task 2 Created", task_id2)
        
        # Run Task
        print("Running Tuffy agent (Expect replan and failure)...")
        r = httpx.post(f"{BASE_URL}/tasks/{task_id2}/run", timeout=300)
        res = r.json()
        print_test("Task 2 Finished Status", res.get("status"))
        print_test("Task 2 Final Error", res.get("error"))
        
        # Check full state
        r_state = httpx.get(f"{BASE_URL}/tasks/{task_id2}")
        print_test("Task 2 Replan Count", r_state.json().get("replan_count"))
    except Exception as e:
        print_test("Test 2 Failed", str(e))
        
    # 4. Clean up
    try:
        httpx.delete(f"{BASE_URL}/documents/{doc_id}")
    except:
        pass
        
    print("\nDone.")

if __name__ == "__main__":
    run_tests()
