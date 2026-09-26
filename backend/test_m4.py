import requests
import json
import os

BASE_URL = "http://localhost:8000/api"

print("--- REGRESSION TESTS ---")

print("1. Health:", requests.get(f"{BASE_URL}/health").json())
print("2. System Status:", requests.get(f"{BASE_URL}/system/status").json())
print("3. Models:", requests.get(f"{BASE_URL}/models").json())

print("4. Inference:")
resp = requests.post(
    f"{BASE_URL}/models/generate", 
    json={"model": "qwen2.5:3b-instruct", "prompt": "Explain what an AI agent is in one sentence."}
)
print("Inference response:", resp.json())

print("\n--- M4 TESTS ---")

# Test 5: Upload valid PDF
with open("test.pdf", "wb") as f:
    f.write(b"%PDF-1.4 test")

with open("test.pdf", "rb") as f:
    resp = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("test.pdf", f, "application/pdf")})
    pdf_upload = resp.json()
    print("5. PDF Upload:", pdf_upload)

doc_id = pdf_upload.get("document_id")

# Test 6: Upload TXT
with open("test.txt", "w") as f:
    f.write("hello")

with open("test.txt", "rb") as f:
    resp = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("test.txt", f, "text/plain")})
    txt_upload = resp.json()
    print("6. TXT Upload:", txt_upload)

# Test 7: Upload unsupported type
with open("test.exe", "wb") as f:
    f.write(b"MZ")

with open("test.exe", "rb") as f:
    resp = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("test.exe", f, "application/x-msdownload")})
    print("7. EXE Upload:", resp.json())

# Test 8: File too large
large_file = b"0" * (51 * 1024 * 1024)  # 51MB
with open("large.txt", "wb") as f:
    f.write(large_file)

with open("large.txt", "rb") as f:
    resp = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("large.txt", f, "text/plain")})
    print("8. Large file upload:", resp.json())

# Test 9: Retrieve metadata
print("9. Get Metadata:", requests.get(f"{BASE_URL}/documents/{doc_id}").json())

# Test 10: Download
resp = requests.get(f"{BASE_URL}/documents/{doc_id}/download")
print("10. Download size:", len(resp.content), "Status code:", resp.status_code)

# Test 11: Delete
resp = requests.delete(f"{BASE_URL}/documents/{doc_id}")
print("11. Delete:", resp.json())

# Test 12: Nonexistent document
print("12. Nonexistent doc:", requests.get(f"{BASE_URL}/documents/does-not-exist").json())

# Cleanup
os.remove("test.pdf")
os.remove("test.txt")
os.remove("test.exe")
os.remove("large.txt")
