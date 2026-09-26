"""
Grounded evidence extraction for approval documents.

SOURCE CHUNKS -> deterministic evidence (fields, measurement tables, observations, each with a source reference)
             -> optional small LLM extraction (findings/actions) that must pass grounding checks
             -> document data where every factual value is traceable to source text or explicitly missing.
"""
import re
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

NOT_PROVIDED = "Not provided in source material."

FIELD_LABELS: Dict[str, List[str]] = {
    "source_document_no": ["Document No.", "Document No", "Document Number", "Report No.", "Report Number"],
    "equipment_id": ["Equipment ID", "Equipment_ID", "Tag No.", "Tag Number"],
    "equipment_name": ["Equipment Name"],
    "equipment": ["Equipment"],
    "inspection_date": ["Inspection Date", "Date of Inspection"],
    "inspection_method": ["Inspection Method"],
    "component": ["Component Examined"],
    "service": ["Service"],
    "department": ["Department"],
    "review_status": ["Review Status"],
    "prepared_by": ["Prepared By"],
    "permit_reference": ["Permit Reference", "Permit No.", "Permit Number", "PTW No."],
    "work_area": ["Work Area"],
    "approver_role": ["Approver Role", "Approving Authority"],
    "baseline_thickness": ["Baseline Thickness"],
    "minimum_allowable_thickness": ["Minimum Allowable Thickness"],
}

ROW_ID = re.compile(r"^[A-Z]{1,3}-?\d{1,3}$")
NUMBER = re.compile(r"^-?\d+(?:\.\d+)?$")
FACT_TOKEN = re.compile(r"[A-Za-z]*\d[\w.\-/]*")
WORD = re.compile(r"[a-z]{4,}")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _source_ref(chunk: Dict[str, Any]) -> Dict[str, Any]:
    return {"document": chunk.get("filename"), "page": chunk.get("page_number"), "chunk_id": chunk.get("chunk_id")}


def _is_value(line: str) -> bool:
    v = line.strip()
    return bool(v) and not re.fullmatch(r"[_\-\s.]+", v) and len(v) <= 120


def extract_fields(chunks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    fields: Dict[str, Dict[str, Any]] = {}
    all_labels = {l.lower() for labels in FIELD_LABELS.values() for l in labels}
    for chunk in chunks:
        lines = [l.strip() for l in (chunk.get("text") or "").splitlines()]
        for i, line in enumerate(lines):
            for key, labels in FIELD_LABELS.items():
                if key in fields:
                    continue
                for label in labels:
                    value = None
                    m = re.fullmatch(rf"{re.escape(label)}\s*:\s*(.+)", line, re.IGNORECASE)
                    # ID-style labels ("Document No. X") may carry the value on the same line without a colon.
                    m_id = re.fullmatch(rf"{re.escape(label)}\s+([A-Z0-9][\w\-/.]*)", line) if label.endswith(("No.", "Number")) else None
                    if m:
                        value = m.group(1)
                    elif m_id:
                        value = m_id.group(1)
                    elif line.lower() == label.lower() and i + 1 < len(lines):
                        value = lines[i + 1]
                    if value and _is_value(value) and value.strip().lower() not in all_labels:
                        fields[key] = {"value": value.strip(), "source": _source_ref(chunk)}
                        break
    return fields


def _merge_headers(headers: List[str], n: int) -> List[str]:
    merged: List[str] = []
    for h in headers:
        if h.startswith("(") and merged:
            merged[-1] = f"{merged[-1]} {h}"
        else:
            merged.append(h)
    while len(merged) > n:
        idx = next((i for i in range(len(merged) - 1) if "(" not in merged[i]), len(merged) - 2)
        merged[idx:idx + 2] = [f"{merged[idx]} {merged[idx + 1]}"]
    return merged if len(merged) == n else [f"Value {i + 1}" for i in range(n)]


def _vertical_table(chunk: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    lines = [l.strip() for l in (chunk.get("text") or "").splitlines() if l.strip()]
    for start, line in enumerate(lines):
        if line.lower() not in ("point", "measurement point", "location"):
            continue
        headers, i = [], start + 1
        while i < len(lines) and not ROW_ID.match(lines[i]):
            headers.append(lines[i])
            i += 1
        rows: List[Dict[str, Any]] = []
        n = None
        while i < len(lines) and ROW_ID.match(lines[i]):
            j = i + 1
            values = []
            while j < len(lines) and NUMBER.match(lines[j]):
                values.append(lines[j])
                j += 1
            if len(values) < 2 or (n is not None and len(values) != n):
                break
            n = len(values)
            rows.append({"point": lines[i], "values": values})
            i = j
        if rows and headers:
            return {"columns": _merge_headers(headers, n), "rows": rows, "source": _source_ref(chunk)}
    return None


def _pipe_table(chunk: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    lines = [l for l in (chunk.get("text") or "").splitlines() if "|" in l]
    if len(lines) < 2:
        return None
    header = [c.strip() for c in lines[0].split("|")]
    point_idx = next((i for i, h in enumerate(header) if "point" in h.lower()), None)
    if point_idx is None:
        return None
    columns = [h for i, h in enumerate(header) if i != point_idx]
    rows = []
    for line in lines[1:]:
        cells = [c.strip() for c in line.split("|")]
        if len(cells) != len(header):
            continue
        rows.append({"point": cells[point_idx], "values": [c for i, c in enumerate(cells) if i != point_idx]})
    return {"columns": columns, "rows": rows, "source": _source_ref(chunk)} if rows else None


def extract_measurements(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tables = []
    for chunk in chunks:
        table = _vertical_table(chunk) or _pipe_table(chunk)
        if table:
            tables.append(table)
    return tables


def extract_observations(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    observations = []
    for chunk in chunks:
        text = _normalize(chunk.get("text"))
        # Bullets only: a dash at the start of the text or directly after a sentence end.
        for part in re.split(r"(?:^|(?<=[.:;])\s+)-\s+(?=[A-Z])", text)[1:]:
            sentence = re.split(r"(?<=\.)\s+(?=\d+\.\s|[A-Z][a-z]+ [a-z]+:)", part.strip())[0]
            if 25 < len(sentence) <= 300 and any(ch.isdigit() for ch in sentence):
                observations.append({"observation": sentence, "source": _source_ref(chunk)})
    return observations


def _column(table: Dict[str, Any], *keywords: str) -> Optional[int]:
    for i, c in enumerate(table["columns"]):
        cl = c.lower()
        if all(k in cl for k in keywords):
            return i
    return None


def derive_checks(tables: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Computed only from extracted source numbers: current thickness vs minimum allowable thickness."""
    checks, blocking = [], []
    for table in tables:
        cur = _column(table, "current")
        mn = _column(table, "min")
        if cur is None or mn is None:
            continue
        per_point, below = [], []
        for row in table["rows"]:
            try:
                current, minimum = float(row["values"][cur]), float(row["values"][mn])
            except (ValueError, IndexError):
                continue
            per_point.append((row["point"], row["values"][cur], row["values"][mn], current - minimum))
            if current < minimum:
                below.append(row["point"])
        if not per_point:
            continue
        lowest = min(per_point, key=lambda p: p[3])
        ref = f"{table['source']['document']} (page {table['source']['page'] or 'N/A'})"
        checks.append({
            "check_id": "CHK-THICKNESS-MIN",
            "name": "Current thickness vs minimum allowable thickness",
            "status": "FAIL" if below else "PASS",
            "evidence": "; ".join(f"{p}: current {c} vs minimum {m}" for p, c, m, _ in per_point)
                        + f". Smallest margin: {lowest[0]} ({lowest[3]:.1f} above minimum)." if not below else
                        f"Below minimum at: {', '.join(below)}",
            "reference": ref,
        })
        for p in below:
            blocking.append({
                "condition": f"{p} current thickness below minimum allowable thickness",
                "status": "BLOCKING", "reason": "Measured value is below the stated minimum.",
                "evidence": ref, "required_action": NOT_PROVIDED, "reference": ref,
            })
        break
    return checks, blocking


def is_supported(text: str, evidence_text: str) -> bool:
    """Every number/ID in text must appear in the evidence, and most content words must too."""
    if not text or not text.strip():
        return False
    ev = _normalize(evidence_text).lower()
    for token in FACT_TOKEN.findall(text):
        t = token.strip(".,;:)(").lower()
        if t and t not in ev:
            return False
    words = WORD.findall(text.lower())
    if not words:
        return True
    return sum(1 for w in words if w in ev) / len(words) >= 0.6


async def llm_findings_and_actions(evidence_text: str) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    from app.core.config import settings
    from app.services.ollama_service import ollama_service
    prompt = (
        "Extract facts from the SOURCE only. Copy wording and numbers exactly. Never add facts.\n"
        'Return JSON: {"findings":[{"observation":"..."}],"required_actions":[{"description":"...","responsible_role":"..."}]}\n'
        "At most 4 findings and 4 actions. If a role is not stated in the SOURCE use \"" + NOT_PROVIDED + "\".\n\n"
        f"SOURCE:\n{evidence_text}\n"
    )
    res = await ollama_service.generate(settings.general_model, prompt, timeout=120, temperature=0.0,
                                        format="json", num_predict=350)
    if "error" in res:
        return {}, res["error"]
    try:
        return json.loads(res.get("response", "")), None
    except json.JSONDecodeError as e:
        return {}, {"code": "LLM_JSON_INVALID", "message": f"Model returned invalid JSON: {e}"}


MAX_DOCUMENT_EVIDENCE_CHARS = 20000


def source_document_chunks(document_ids: List[str]) -> List[Dict[str, Any]]:
    """All indexed chunks of the retrieved source documents, for deterministic extraction (no model cost)."""
    from app.services.vector_store import vector_store
    from app.services.document_service import document_service
    chunks, total = [], 0
    for doc_id in document_ids:
        meta = document_service.get_metadata(doc_id)
        filename = meta.get("original_filename", doc_id) if "error" not in meta else doc_id
        for m in vector_store.metadata:
            if m.get("document_id") != doc_id:
                continue
            text = m.get("text") or ""
            if total + len(text) > MAX_DOCUMENT_EVIDENCE_CHARS:
                return chunks
            total += len(text)
            chunks.append({"document_id": doc_id, "filename": filename, "page_number": (m.get("source") or {}).get("page"),
                           "chunk_id": m.get("chunk_id"), "text": text})
    return chunks


async def build_document_data(task_id: str, evidence: List[Dict[str, Any]], use_llm: bool = True,
                              document_chunks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """evidence: top-k retrieved chunks (sent to the model). document_chunks: full retrieved documents (deterministic only)."""
    evidence = [e for e in evidence if (e.get("text") or "").strip()]
    evidence_text = "\n\n".join(e["text"] for e in evidence)
    extraction_chunks = [c for c in (document_chunks or []) if (c.get("text") or "").strip()] or evidence
    grounding_text = "\n\n".join(c["text"] for c in extraction_chunks) + "\n\n" + evidence_text
    fields = extract_fields(extraction_chunks)
    tables = extract_measurements(extraction_chunks)
    observations = extract_observations(extraction_chunks)
    checks, blocking = derive_checks(tables)
    warnings: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    def field(key: str) -> str:
        return fields[key]["value"] if key in fields else NOT_PROVIDED

    findings = [
        {"finding_id": f"F-{i + 1}", "observation": o["observation"], "evidence": "Stated in source",
         "reference": f"{o['source']['document']} (page {o['source']['page'] or 'N/A'})"}
        for i, o in enumerate(observations)
    ]
    actions: List[Dict[str, Any]] = []

    if use_llm and evidence_text:
        llm, llm_error = await llm_findings_and_actions(evidence_text)
        if llm_error:
            warnings.append({"stage": "llm_extraction", **llm_error})
        for f in llm.get("findings") or []:
            obs = _normalize((f or {}).get("observation", "")) if isinstance(f, dict) else ""
            if not obs:
                continue
            if not is_supported(obs, grounding_text):
                rejected.append({"field": "finding", "value": obs, "reason": "not supported by source evidence"})
            elif not any(obs.lower() in x["observation"].lower() or x["observation"].lower() in obs.lower() for x in findings):
                findings.append({"finding_id": f"F-{len(findings) + 1}", "observation": obs,
                                 "evidence": "Model-extracted, verified against source text", "reference": "Retrieved source excerpts"})
        for a in llm.get("required_actions") or []:
            desc = _normalize((a or {}).get("description", "")) if isinstance(a, dict) else ""
            if not desc:
                continue
            if not is_supported(desc, grounding_text):
                rejected.append({"field": "required_action", "value": desc, "reason": "not supported by source evidence"})
                continue
            role = _normalize(a.get("responsible_role", ""))
            if role and role != NOT_PROVIDED and role.lower() not in grounding_text.lower():
                rejected.append({"field": "responsible_role", "value": role, "reason": "role not stated in source"})
                role = NOT_PROVIDED
            actions.append({"description": desc, "responsible_role": role or NOT_PROVIDED})

    equipment_parts = [field("equipment_id"), field("equipment_name") if "equipment_name" in fields else field("equipment")]
    equipment = " — ".join(dict.fromkeys(p for p in equipment_parts if p != NOT_PROVIDED)) or NOT_PROVIDED
    sources = []
    for e in extraction_chunks:
        ref = f"{e.get('filename')} (page {e.get('page_number') or 'N/A'}, {e.get('chunk_id')})"
        if ref not in sources:
            sources.append(ref)

    facts_count = len(fields) + sum(len(t["rows"]) for t in tables) + len(findings)
    data = {
        "document_type": "Inspection Approval Note",
        "title": f"{equipment} — Inspection Approval Note" if equipment != NOT_PROVIDED else "INSPECTION APPROVAL NOTE",
        "document_id": f"DRAFT-{task_id}",
        "permit_reference": field("permit_reference"),
        "equipment": equipment,
        "source_report": field("source_document_no"),
        "inspection_date": field("inspection_date"),
        "inspection_method": field("inspection_method"),
        "permit_details": {
            "work_area": field("work_area") if "work_area" in fields else field("component"),
            "requested_extension": NOT_PROVIDED,
            "current_status": field("review_status"),
            "requested_by": field("prepared_by"),
            "approver_role": field("approver_role"),
        },
        "agent_checks": checks,
        "findings": findings,
        "measurements": tables,
        "blocking_conditions": blocking,
        "regulatory_references": [],
        "required_actions": actions,
        "approval": {"approver_role": field("approver_role")},
        "status": "PENDING HUMAN",
        "provenance": {
            "agent": "Tuffy (Sovereign AI Workbench, local inference)",
            "source_documents": sources,
            "field_sources": {k: v["source"] for k, v in fields.items()},
            "warnings": warnings,
            "rejected_values": rejected,
        },
    }
    grounding = {
        "evidence_chunks": len(evidence),
        "document_chunks_scanned": len(extraction_chunks),
        "facts_from_source": facts_count,
        "fields_extracted": sorted(fields.keys()),
        "measurement_rows": sum(len(t["rows"]) for t in tables),
        "rejected_values": rejected,
        "warnings": warnings,
    }
    return {"data": data, "grounding": grounding}
