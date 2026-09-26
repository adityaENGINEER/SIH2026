import httpx
import time
import os

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

    print("\n--- M8 TESTS (RAG) ---")
    
    # 1. Upload Doc A
    try:
        files_a = {'file': ('doc_a.txt', b'Inspection found excessive vibration in Pump P-101.', 'text/plain')}
        doc_a_id = httpx.post(f"{BASE_URL}/documents/upload", files=files_a).json().get("document_id")
        httpx.get(f"{BASE_URL}/documents/{doc_a_id}/content")
        httpx.post(f"{BASE_URL}/knowledge/index", json={"document_id": doc_a_id}, timeout=120)
        print_test("Indexed Document A", doc_a_id)
    except Exception as e:
        print_test("Doc A Failed", str(e))
        return
        
    # 2. Upload Doc B
    try:
        files_b = {'file': ('doc_b.txt', b'Finance department approved the annual procurement budget of Rs 500000.', 'text/plain')}
        doc_b_id = httpx.post(f"{BASE_URL}/documents/upload", files=files_b).json().get("document_id")
        httpx.get(f"{BASE_URL}/documents/{doc_b_id}/content")
        httpx.post(f"{BASE_URL}/knowledge/index", json={"document_id": doc_b_id}, timeout=120)
        print_test("Indexed Document B", doc_b_id)
    except Exception as e:
        print_test("Doc B Failed", str(e))
        return

    # 3. RAG Query (Pump)
    try:
        print("\nQuerying: What problem was found in the pump?")
        r = httpx.post(f"{BASE_URL}/knowledge/query", json={"query": "What problem was found in the pump?", "top_k": 3}, timeout=120)
        res = r.json()
        print_test("RAG Answer (Pump)", res.get("answer"))
        print_test("Grounded", res.get("grounded"))
        print_test("Sources Retrieved", res.get("retrieval", {}).get("results_found"))
    except Exception as e:
        print_test("Query 1 Failed", str(e))

    # 4. RAG Query (No Context / Hallucination check)
    try:
        print("\nQuerying: What is the manufacturing cost of the pump?")
        r = httpx.post(f"{BASE_URL}/knowledge/query", json={"query": "What is the manufacturing cost of the pump?", "top_k": 3}, timeout=120)
        res = r.json()
        print_test("RAG Answer (Cost)", res.get("answer"))
        print_test("Grounded", res.get("grounded"))
        print_test("Sources Retrieved", res.get("retrieval", {}).get("results_found"))
    except Exception as e:
        print_test("Query 2 Failed", str(e))

    # 5. Delete Document Test
    try:
        print(f"\nDeleting Document B: {doc_b_id}")
        httpx.delete(f"{BASE_URL}/documents/{doc_b_id}")
        r = httpx.post(f"{BASE_URL}/knowledge/search", json={"query": "Finance budget", "top_k": 2})
        search_res = r.json()
        found_doc_b = any(res.get("document_id") == doc_b_id for res in search_res.get("results", []))
        print_test("Document B still in vector store?", found_doc_b)
    except Exception as e:
        print_test("Delete Test Failed", str(e))
        
    print("\nDone.")

if __name__ == "__main__":
    run_tests()
