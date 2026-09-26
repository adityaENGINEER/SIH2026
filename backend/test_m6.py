import requests
import json
import os
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont

BASE_URL = "http://localhost:8000/api"

print("--- REGRESSION TESTS ---")
print("1. Health:", requests.get(f"{BASE_URL}/health").json())
print("2. System Status:", requests.get(f"{BASE_URL}/system/status").json())
print("3. Models:", requests.get(f"{BASE_URL}/models").json())

print("\n--- M6 TESTS ---")

# 1. Create a scanned PDF simulation (just empty PDF since Tesseract won't run anyway, but let's make an image-based PDF to be thorough)
img = Image.new('RGB', (400, 200), color=(255, 255, 255))
d = ImageDraw.Draw(img)
d.text((10,10), "SOVEREIGN AI WORKBENCH\nOCR TEST\nInspection Report", fill=(0,0,0))
img.save("ocr_test.png")

pdf = FPDF()
pdf.add_page()
pdf.image("ocr_test.png", x=10, y=10, w=100)
pdf.output("test_scanned.pdf")

# 2. Upload the scanned PDF
with open("test_scanned.pdf", "rb") as f:
    resp = requests.post(f"{BASE_URL}/documents/upload", files={"file": ("test_scanned.pdf", f, "application/pdf")})
    scanned_upload = resp.json()

doc_id = scanned_upload.get("document_id")
print("Scanned PDF Upload:", scanned_upload)

# 3. Trigger M5 extraction, it should say requires_ocr = True
resp = requests.get(f"{BASE_URL}/documents/{doc_id}/content")
print("M5 Extraction Result:", resp.json())

# 4. Trigger M6 OCR
print("Triggering OCR...")
resp = requests.post(f"{BASE_URL}/ocr/process", json={"document_id": doc_id})
ocr_result = resp.json()
print("OCR Process Result:", ocr_result)

# Cleanup
requests.delete(f"{BASE_URL}/documents/{doc_id}")
os.remove("test_scanned.pdf")
os.remove("ocr_test.png")

print("Done.")
