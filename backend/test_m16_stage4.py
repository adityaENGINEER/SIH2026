# -*- coding: utf-8 -*-
"""
M16 Stage 4 - Approval Lifecycle + Deliverables tests.

Run with: python -u test_m16_stage4.py
Server must be running on localhost:8000.
"""
import os
import time
import httpx

BASE_URL = "http://localhost:8000/api"

# Shared state
project_a_id = None
project_b_id = None
approval_id = None
deliverable_docx_id = None
deliverable_pdf_id = None
deliverable_pptx_id = None
deliverable_xlsx_id = None

CONTENT = "This is a test deliverable.\nIt contains multiple lines.\nLine 3.\nLine 4."


# ==========================================================================
# Helpers
# ==========================================================================
def create_project(name: str) -> str:
    res = httpx.post(f"{BASE_URL}/projects", json={"name": name, "description": "test", "project_type": "test"})
    assert res.status_code == 200, res.text
    return res.json()["project_id"]


def _assert_error(res, expected_code: str):
    assert res.status_code in (400, 404), f"Expected 400/404, got {res.status_code}: {res.text}"
    detail = res.json().get("detail", {})
    assert detail.get("code") == expected_code, f"Expected {expected_code}, got {detail}"


# ==========================================================================
# APPROVAL TESTS
# ==========================================================================

def test_01_create_approval():
    global approval_id, project_a_id
    project_a_id = create_project("Stage4ProjectA")
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals", json={
        "title": "Safety Inspection Authorization",
        "task_id": "task_test_001",
        "source_document_ids": ["doc_abc", "doc_def"]
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "DRAFT"
    assert data["project_id"] == project_a_id
    assert data["signature_status"] == "unsigned"
    approval_id = data["approval_id"]
    print(f"  [PASS] Create approval: {approval_id}")


def test_02_get_approval():
    res = httpx.get(f"{BASE_URL}/projects/{project_a_id}/approvals/{approval_id}")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["approval_id"] == approval_id
    assert data["status"] == "DRAFT"
    print("  [PASS] Get approval")


def test_03_list_approvals():
    res = httpx.get(f"{BASE_URL}/projects/{project_a_id}/approvals")
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert any(a["approval_id"] == approval_id for a in data)
    print(f"  [PASS] List approvals ({len(data)} found)")


def test_04_submit_for_review():
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals/{approval_id}/submit")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "PENDING_HUMAN_SIGNOFF"
    assert data["submitted_at"] is not None
    print("  [PASS] Submit for review")


def test_05_invalid_double_submit():
    """Cannot submit again once already PENDING."""
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals/{approval_id}/submit")
    _assert_error(res, "INVALID_APPROVAL_STATE")
    print("  [PASS] Invalid double-submit blocked")


def test_06_approve():
    res = httpx.post(
        f"{BASE_URL}/projects/{project_a_id}/approvals/{approval_id}/approve",
        json={"approver_name": "Jane Smith", "employee_id": "EMP-1234", "reason": "All checks passed.", "comment": "Approved after inspection."}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "APPROVED"
    assert data["approver_name"] == "Jane Smith"
    assert data["employee_id"] == "EMP-1234"
    assert data["approval_reason"] == "All checks passed."
    assert data["signature_status"] == "signed"
    assert data["reviewed_at"] is not None
    print("  [PASS] Approve with human metadata persisted")


def test_07_approve_already_approved():
    """Cannot approve a terminal APPROVED state."""
    res = httpx.post(
        f"{BASE_URL}/projects/{project_a_id}/approvals/{approval_id}/approve",
        json={"approver_name": "Bob", "employee_id": "EMP-999"}
    )
    _assert_error(res, "INVALID_APPROVAL_STATE")
    print("  [PASS] Terminal APPROVED state re-approval blocked")


def test_08_reject_from_draft_fails():
    """DRAFT â†’ REJECTED must be rejected."""
    new_appr = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals", json={"title": "Test Reject Draft"})
    assert new_appr.status_code == 200
    bad_id = new_appr.json()["approval_id"]
    res = httpx.post(
        f"{BASE_URL}/projects/{project_a_id}/approvals/{bad_id}/reject",
        json={"approver_name": "Bob", "employee_id": "EMP-999", "reason": "bad"}
    )
    _assert_error(res, "INVALID_APPROVAL_STATE")
    print("  [PASS] DRAFT -> REJECTED blocked")


def test_09_reject_flow():
    """Test full reject flow: DRAFT â†’ PENDING â†’ REJECTED."""
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals", json={"title": "Rejection Test"})
    assert res.status_code == 200
    rid = res.json()["approval_id"]

    httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals/{rid}/submit")

    res = httpx.post(
        f"{BASE_URL}/projects/{project_a_id}/approvals/{rid}/reject",
        json={"approver_name": "Inspector X", "employee_id": "EMP-007", "reason": "Conditions not met.", "comment": "Review again."}
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["status"] == "REJECTED"
    assert data["rejection_reason"] == "Conditions not met."
    assert data["approver_name"] == "Inspector X"
    assert data["employee_id"] == "EMP-007"
    print("  [PASS] Reject flow with metadata persistence")


def test_10_missing_approval():
    res = httpx.get(f"{BASE_URL}/projects/{project_a_id}/approvals/appr_doesnotexist")
    assert res.status_code == 404, res.text
    print("  [PASS] Missing approval -> 404")


def test_11_project_isolation_approvals():
    global project_b_id
    project_b_id = create_project("Stage4ProjectB")
    # Project B cannot read Project A's approval
    res = httpx.get(f"{BASE_URL}/projects/{project_b_id}/approvals/{approval_id}")
    assert res.status_code == 404, f"Isolation failure: got {res.status_code}"
    # Project B approvals list must be empty (nothing created there yet)
    res2 = httpx.get(f"{BASE_URL}/projects/{project_b_id}/approvals")
    assert res2.status_code == 200
    assert len(res2.json()) == 0
    print("  [PASS] Project isolation for approvals enforced")


# ==========================================================================
# DELIVERABLE TESTS
# ==========================================================================

def test_12_generate_docx():
    global deliverable_docx_id
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/deliverables", json={
        "project_id": project_a_id,
        "title": "Safety Report DOCX",
        "format": "DOCX",
        "content": CONTENT
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["type"] == "DOCX"
    assert data["status"] == "ready"
    assert data["size"] > 0
    assert os.path.exists(data["path"])
    deliverable_docx_id = data["deliverable_id"]
    print(f"  [PASS] Generate DOCX: {deliverable_docx_id} ({data['size']} bytes)")


def test_13_generate_pdf():
    global deliverable_pdf_id
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/deliverables", json={
        "project_id": project_a_id,
        "title": "Safety Report PDF",
        "format": "PDF",
        "content": CONTENT
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["type"] == "PDF"
    assert data["status"] == "ready"
    assert data["size"] > 0
    assert os.path.exists(data["path"])
    deliverable_pdf_id = data["deliverable_id"]
    print(f"  [PASS] Generate PDF: {deliverable_pdf_id} ({data['size']} bytes)")


def test_14_generate_pptx():
    global deliverable_pptx_id
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/deliverables", json={
        "project_id": project_a_id,
        "title": "Safety Report PPTX",
        "format": "PPTX",
        "content": CONTENT
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["type"] == "PPTX"
    assert data["status"] == "ready"
    assert data["size"] > 0
    assert os.path.exists(data["path"])
    deliverable_pptx_id = data["deliverable_id"]
    print(f"  [PASS] Generate PPTX: {deliverable_pptx_id} ({data['size']} bytes)")


def test_15_generate_xlsx():
    global deliverable_xlsx_id
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/deliverables", json={
        "project_id": project_a_id,
        "title": "Safety Report XLSX",
        "format": "XLSX",
        "content": CONTENT
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["type"] == "XLSX"
    assert data["status"] == "ready"
    assert data["size"] > 0
    assert os.path.exists(data["path"])
    deliverable_xlsx_id = data["deliverable_id"]
    print(f"  [PASS] Generate XLSX: {deliverable_xlsx_id} ({data['size']} bytes)")


def test_16_get_deliverable_metadata():
    res = httpx.get(f"{BASE_URL}/projects/{project_a_id}/deliverables/{deliverable_docx_id}")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["deliverable_id"] == deliverable_docx_id
    assert data["project_id"] == project_a_id
    assert data["type"] == "DOCX"
    print("  [PASS] Get deliverable metadata")


def test_17_list_deliverables():
    res = httpx.get(f"{BASE_URL}/projects/{project_a_id}/deliverables")
    assert res.status_code == 200, res.text
    data = res.json()
    assert len(data) >= 4
    ids = {d["deliverable_id"] for d in data}
    assert deliverable_docx_id in ids
    assert deliverable_pdf_id in ids
    assert deliverable_pptx_id in ids
    assert deliverable_xlsx_id in ids
    print(f"  [PASS] List deliverables ({len(data)} found)")


def test_18_download_docx():
    res = httpx.get(f"{BASE_URL}/projects/{project_a_id}/deliverables/{deliverable_docx_id}/download")
    assert res.status_code == 200, res.text
    assert len(res.content) > 0
    print(f"  [PASS] Download DOCX ({len(res.content)} bytes)")


def test_19_download_pdf():
    res = httpx.get(f"{BASE_URL}/projects/{project_a_id}/deliverables/{deliverable_pdf_id}/download")
    assert res.status_code == 200, res.text
    assert res.content[:4] == b"%PDF"  # PDF magic bytes
    print(f"  [PASS] Download PDF ({len(res.content)} bytes, magic OK)")


def test_20_download_pptx():
    res = httpx.get(f"{BASE_URL}/projects/{project_a_id}/deliverables/{deliverable_pptx_id}/download")
    assert res.status_code == 200, res.text
    assert len(res.content) > 0
    print(f"  [PASS] Download PPTX ({len(res.content)} bytes)")


def test_21_download_xlsx():
    res = httpx.get(f"{BASE_URL}/projects/{project_a_id}/deliverables/{deliverable_xlsx_id}/download")
    assert res.status_code == 200, res.text
    assert len(res.content) > 0
    print(f"  [PASS] Download XLSX ({len(res.content)} bytes)")


def test_22_invalid_format():
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/deliverables", json={
        "project_id": project_a_id,
        "title": "Bad Format",
        "format": "MP4",
        "content": "whatever"
    })
    _assert_error(res, "UNSUPPORTED_FORMAT")
    print("  [PASS] Invalid format rejected")


def test_23_project_isolation_deliverables():
    """Project B cannot read or download Project A's deliverables."""
    res = httpx.get(f"{BASE_URL}/projects/{project_b_id}/deliverables/{deliverable_docx_id}")
    assert res.status_code == 404, f"Isolation failure: got {res.status_code}"

    res2 = httpx.get(f"{BASE_URL}/projects/{project_b_id}/deliverables/{deliverable_pdf_id}/download")
    assert res2.status_code == 404, f"Download isolation failure: got {res2.status_code}"

    res3 = httpx.get(f"{BASE_URL}/projects/{project_b_id}/deliverables")
    assert res3.status_code == 200
    assert len(res3.json()) == 0
    print("  [PASS] Project isolation for deliverables enforced")


# ==========================================================================
# INTEGRATION TESTS
# ==========================================================================

def test_24_deliverable_linked_to_approval():
    """Create a deliverable then link it to a new approval."""
    # New deliverable for project A
    res = httpx.post(f"{BASE_URL}/projects/{project_a_id}/deliverables", json={
        "project_id": project_a_id,
        "title": "Linked Report",
        "format": "PDF",
        "content": "Linked integration test content."
    })
    assert res.status_code == 200, res.text
    dlvr = res.json()
    dlvr_id = dlvr["deliverable_id"]

    # Create approval referencing this deliverable
    res2 = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals", json={
        "title": "Linked Approval",
        "deliverable_id": dlvr_id,
        "output_document_ids": [dlvr_id]
    })
    assert res2.status_code == 200, res2.text
    appr = res2.json()
    assert appr["deliverable_id"] == dlvr_id
    print(f"  [PASS] Deliverable->Approval link: {dlvr_id} -> {appr['approval_id']}")
    return appr["approval_id"]


def test_25_full_integration_lifecycle():
    """Full: create deliverable â†’ create approval â†’ submit â†’ approve."""
    # Step 1: Deliverable
    r1 = httpx.post(f"{BASE_URL}/projects/{project_a_id}/deliverables", json={
        "project_id": project_a_id,
        "title": "Integration DOCX",
        "format": "DOCX",
        "content": "Full integration lifecycle test document."
    })
    assert r1.status_code == 200, r1.text
    dlvr = r1.json()
    assert os.path.exists(dlvr["path"])

    # Step 2: Approval
    r2 = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals", json={
        "title": "Integration Approval",
        "deliverable_id": dlvr["deliverable_id"]
    })
    assert r2.status_code == 200, r2.text
    appr_id = r2.json()["approval_id"]
    assert r2.json()["status"] == "DRAFT"

    # Step 3: Submit (AI/system action â€” transitions to PENDING, NOT APPROVED)
    r3 = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals/{appr_id}/submit")
    assert r3.status_code == 200, r3.text
    assert r3.json()["status"] == "PENDING_HUMAN_SIGNOFF"

    # Step 4: Human approve
    r4 = httpx.post(
        f"{BASE_URL}/projects/{project_a_id}/approvals/{appr_id}/approve",
        json={"approver_name": "Alice Doe", "employee_id": "EMP-4321", "reason": "Integration test pass."}
    )
    assert r4.status_code == 200, r4.text
    final = r4.json()
    assert final["status"] == "APPROVED"
    assert final["approver_name"] == "Alice Doe"
    assert final["employee_id"] == "EMP-4321"
    assert final["signature_status"] == "signed"
    assert final["reviewed_at"] is not None
    print("  [PASS] Full integration lifecycle: Deliverable->Draft->Pending->APPROVED")


def test_26_full_rejection_lifecycle():
    """Full: create â†’ submit â†’ reject."""
    r1 = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals", json={"title": "Rejection Integration"})
    assert r1.status_code == 200
    rid = r1.json()["approval_id"]

    r2 = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals/{rid}/submit")
    assert r2.status_code == 200

    r3 = httpx.post(
        f"{BASE_URL}/projects/{project_a_id}/approvals/{rid}/reject",
        json={"approver_name": "Safety Officer", "employee_id": "SO-001", "reason": "Non-compliant."}
    )
    assert r3.status_code == 200
    final = r3.json()
    assert final["status"] == "REJECTED"
    assert final["rejection_reason"] == "Non-compliant."
    assert final["approver_name"] == "Safety Officer"
    print("  [PASS] Full rejection lifecycle with metadata persistence")


def test_27_cross_project_lifecycle_isolation():
    """Ensure project B cannot tamper with project A's approval workflow."""
    r1 = httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals", json={"title": "Isolation Lifecycle"})
    assert r1.status_code == 200
    aid = r1.json()["approval_id"]

    httpx.post(f"{BASE_URL}/projects/{project_a_id}/approvals/{aid}/submit")

    # Project B tries to approve
    r_bad = httpx.post(
        f"{BASE_URL}/projects/{project_b_id}/approvals/{aid}/approve",
        json={"approver_name": "Hacker", "employee_id": "H-000"}
    )
    assert r_bad.status_code == 404, f"Cross-project isolation failed: {r_bad.status_code}"
    print("  [PASS] Cross-project approval tampering blocked")


# ==========================================================================
# Runner
# ==========================================================================
if __name__ == "__main__":
    tests = [
        ("01 Create Approval", test_01_create_approval),
        ("02 Get Approval", test_02_get_approval),
        ("03 List Approvals", test_03_list_approvals),
        ("04 Submit for Review", test_04_submit_for_review),
        ("05 Invalid Double Submit", test_05_invalid_double_submit),
        ("06 Approve with Metadata", test_06_approve),
        ("07 Re-approve Terminal Blocked", test_07_approve_already_approved),
        ("08 Reject from DRAFT Fails", test_08_reject_from_draft_fails),
        ("09 Reject Flow", test_09_reject_flow),
        ("10 Missing Approval 404", test_10_missing_approval),
        ("11 Project Isolation Approvals", test_11_project_isolation_approvals),
        ("12 Generate DOCX", test_12_generate_docx),
        ("13 Generate PDF", test_13_generate_pdf),
        ("14 Generate PPTX", test_14_generate_pptx),
        ("15 Generate XLSX", test_15_generate_xlsx),
        ("16 Get Deliverable Metadata", test_16_get_deliverable_metadata),
        ("17 List Deliverables", test_17_list_deliverables),
        ("18 Download DOCX", test_18_download_docx),
        ("19 Download PDF", test_19_download_pdf),
        ("20 Download PPTX", test_20_download_pptx),
        ("21 Download XLSX", test_21_download_xlsx),
        ("22 Invalid Format", test_22_invalid_format),
        ("23 Project Isolation Deliverables", test_23_project_isolation_deliverables),
        ("24 Deliverable Linked to Approval", test_24_deliverable_linked_to_approval),
        ("25 Full Integration Lifecycle", test_25_full_integration_lifecycle),
        ("26 Full Rejection Lifecycle", test_26_full_rejection_lifecycle),
        ("27 Cross-project Isolation", test_27_cross_project_lifecycle_isolation),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Stage 4 Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed == 0:
        print("ALL STAGE 4 TESTS PASSED")
    else:
        import sys
        sys.exit(1)

