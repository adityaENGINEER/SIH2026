import httpx
import time
import os
import numpy as np

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

    try:
        r = httpx.post(f"{BASE_URL}/models/generate", json={"model": "qwen2.5:3b-instruct", "prompt": "Say hello"})
        print_test("Inference", r.status_code == 200)
    except Exception as e:
        print_test("Inference Failed", str(e))
        
    print("\n--- M7 TESTS ---")
    
    # Upload a document
    doc_id = None
    try:
        files = {'file': ('test_doc.txt', b'Inspection found excessive vibration in Pump P-101.\n\nFinance department approved the annual procurement budget.', 'text/plain')}
        r = httpx.post(f"{BASE_URL}/documents/upload", files=files)
        upload_result = r.json()
        print_test("TXT Upload", upload_result)
        doc_id = upload_result.get("document_id")
    except Exception as e:
        print_test("TXT Upload Failed", str(e))
        return
        
    if not doc_id:
        print("Missing document ID, stopping.")
        return
        
    # Extract
    try:
        r = httpx.get(f"{BASE_URL}/documents/{doc_id}/content")
        print_test("Content Extraction", "text" in r.json().get("content", {}))
    except Exception as e:
        print_test("Content Extraction Failed", str(e))
        
    # Index
    try:
        r = httpx.post(f"{BASE_URL}/knowledge/index", json={"document_id": doc_id})
        index_result = r.json()
        print_test("Indexing Result", index_result)
    except Exception as e:
        print_test("Indexing Failed", str(e))
        
    # Test Empty Document
    try:
        files = {'file': ('empty.txt', b'', 'text/plain')}
        r = httpx.post(f"{BASE_URL}/documents/upload", files=files)
        empty_id = r.json().get("document_id")
        httpx.get(f"{BASE_URL}/documents/{empty_id}/content")
        r = httpx.post(f"{BASE_URL}/knowledge/index", json={"document_id": empty_id})
        print_test("Empty Indexing", r.json())
    except Exception as e:
        print_test("Empty Indexing Failed", str(e))
        
    # Test Duplicate Indexing
    try:
        r = httpx.post(f"{BASE_URL}/knowledge/index", json={"document_id": doc_id})
        print_test("Duplicate Indexing", r.json())
    except Exception as e:
        print_test("Duplicate Indexing Failed", str(e))

    # Semantic Search
    try:
        r = httpx.post(f"{BASE_URL}/knowledge/search", json={"query": "What problem was found in the pump?", "top_k": 2})
        search_result = r.json()
        print_test("Search Result", search_result)
        
        found_pump = False
        for res in search_result.get("results", []):
            if "Pump P-101" in res.get("text", ""):
                found_pump = True
                break
        print_test("Semantic Relevance (Pump Found)", found_pump)
    except Exception as e:
        print_test("Search Failed", str(e))
        
    print("\nDone.")

if __name__ == "__main__":
    run_tests()
