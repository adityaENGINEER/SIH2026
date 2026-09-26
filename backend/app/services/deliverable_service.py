"""
Deliverable service — local filesystem persistence only.
Storage: D:\\SovereignAI\\storage\\outputs\\{project_id}\\{deliverable_id}\\

Supported formats: DOCX, PDF, PPTX, XLSX
Uses existing M12 DOCX generator for DOCX output.
Uses ReportLab for PDF, python-pptx for PPTX, openpyxl for XLSX.
"""
import os
import json
import uuid
import logging
import re
import shutil
from datetime import datetime
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {"DOCX", "PDF", "PPTX", "XLSX"}


def _safe_filename(name: str) -> str:
    """Strip path-traversal characters and limit length."""
    name = re.sub(r"[^\w\-. ]", "_", name)
    name = name.replace(" ", "_")
    return name[:80]


class DeliverableService:
    def __init__(self):
        self.outputs_dir = os.path.join(settings.storage_root, "outputs")
        os.makedirs(self.outputs_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    def _project_dir(self, project_id: str) -> str:
        p = os.path.join(self.outputs_dir, project_id)
        if not os.path.abspath(p).startswith(os.path.abspath(self.outputs_dir)):
            raise ValueError("Invalid project_id path.")
        return p

    def _deliverable_dir(self, project_id: str, deliverable_id: str) -> str:
        d = os.path.join(self._project_dir(project_id), deliverable_id)
        if not os.path.abspath(d).startswith(os.path.abspath(self.outputs_dir)):
            raise ValueError("Invalid deliverable_id path.")
        return d

    def _meta_path(self, project_id: str, deliverable_id: str) -> str:
        return os.path.join(self._deliverable_dir(project_id, deliverable_id), "metadata.json")

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

    def _save_meta(self, meta: dict):
        project_id = meta["project_id"]
        deliverable_id = meta["deliverable_id"]
        d = self._deliverable_dir(project_id, deliverable_id)
        os.makedirs(d, exist_ok=True)
        with open(self._meta_path(project_id, deliverable_id), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def _load_meta(self, project_id: str, deliverable_id: str) -> Optional[dict]:
        path = self._meta_path(project_id, deliverable_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # ------------------------------------------------------------------
    # File generators
    # ------------------------------------------------------------------
    def _generate_docx(self, file_path: str, title: str, content: str):
        """Reuse existing M12 python-docx setup, minimal standalone version."""
        from docx import Document
        from docx.shared import Pt
        doc = Document()
        doc.add_heading(title, 0)
        doc.add_paragraph(f"Generated: {datetime.utcnow().isoformat()}Z")
        doc.add_paragraph("")
        for line in content.splitlines():
            doc.add_paragraph(line)
        doc.add_paragraph("")
        footer_p = doc.add_paragraph()
        footer_r = footer_p.add_run(
            "AI-GENERATED DOCUMENT — Requires human review and sign-off before operational use."
        )
        footer_r.bold = True
        doc.save(file_path)

    def _generate_pdf(self, file_path: str, title: str, content: str):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas as pdf_canvas

        c = pdf_canvas.Canvas(file_path, pagesize=A4)
        width, height = A4
        margin = 2 * cm
        y = height - margin

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, y, title[:80])
        y -= 0.8 * cm

        # Timestamp
        c.setFont("Helvetica", 9)
        c.drawString(margin, y, f"Generated: {datetime.utcnow().isoformat()}Z")
        y -= 0.6 * cm
        c.line(margin, y, width - margin, y)
        y -= 0.5 * cm

        # Body
        c.setFont("Helvetica", 11)
        line_height = 0.5 * cm
        for line in content.splitlines():
            if y < margin + line_height:
                c.showPage()
                y = height - margin
                c.setFont("Helvetica", 11)
            # Wrap long lines
            while len(line) > 90:
                c.drawString(margin, y, line[:90])
                y -= line_height
                line = line[90:]
                if y < margin + line_height:
                    c.showPage()
                    y = height - margin
                    c.setFont("Helvetica", 11)
            c.drawString(margin, y, line)
            y -= line_height

        # Footer
        y -= 0.3 * cm
        c.setFont("Helvetica-Bold", 9)
        c.drawString(
            margin,
            margin,
            "AI-GENERATED — Requires human review before use.",
        )
        c.save()

    def _generate_pptx(self, file_path: str, title: str, content: str):
        from pptx import Presentation
        from pptx.util import Inches, Pt

        prs = Presentation()
        # Title slide
        slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(slide_layout)
        slide.shapes.title.text = title
        slide.placeholders[1].text = f"Generated: {datetime.utcnow().isoformat()}Z"

        # Content slides (one per paragraph block, chunked)
        lines = [l for l in content.splitlines() if l.strip()]
        chunk_size = 10
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i : i + chunk_size]
            content_layout = prs.slide_layouts[1]
            s = prs.slides.add_slide(content_layout)
            s.shapes.title.text = f"{title} (cont.)" if i > 0 else title
            tf = s.placeholders[1].text_frame
            tf.text = chunk[0]
            for line in chunk[1:]:
                tf.add_paragraph().text = line

        # Disclaimer slide
        disc_layout = prs.slide_layouts[5]
        disc_slide = prs.slides.add_slide(disc_layout)
        tx_box = disc_slide.shapes.add_textbox(Inches(0.5), Inches(2), Inches(9), Inches(2))
        tf = tx_box.text_frame
        tf.text = "AI-GENERATED DOCUMENT — Requires human review and sign-off before operational use."

        prs.save(file_path)

    def _generate_xlsx(self, file_path: str, title: str, content: str):
        from openpyxl import Workbook
        from openpyxl.styles import Font

        wb = Workbook()
        ws = wb.active
        ws.title = "Deliverable"

        # Header row
        ws.cell(row=1, column=1, value=title).font = Font(bold=True, size=14)
        ws.cell(row=2, column=1, value=f"Generated: {datetime.utcnow().isoformat()}Z")
        ws.cell(row=3, column=1, value="")

        row_idx = 4
        for line in content.splitlines():
            ws.cell(row=row_idx, column=1, value=line)
            row_idx += 1

        ws.cell(row=row_idx + 1, column=1, value="AI-GENERATED — Requires human review.").font = Font(
            bold=True, color="FF0000"
        )
        wb.save(file_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_deliverable(
        self,
        project_id: str,
        title: str,
        fmt: str,
        content: str = "",
        task_id: Optional[str] = None,
        approval_id: Optional[str] = None,
    ) -> dict:
        fmt = fmt.upper()
        if fmt not in SUPPORTED_FORMATS:
            return {
                "error": {
                    "code": "UNSUPPORTED_FORMAT",
                    "message": f"Format '{fmt}' is not supported. Use one of: {sorted(SUPPORTED_FORMATS)}",
                }
            }

        deliverable_id = f"dlvr_{uuid.uuid4().hex[:12]}"
        d_dir = self._deliverable_dir(project_id, deliverable_id)
        os.makedirs(d_dir, exist_ok=True)

        safe_title = _safe_filename(title)
        ext_map = {"DOCX": ".docx", "PDF": ".pdf", "PPTX": ".pptx", "XLSX": ".xlsx"}
        filename = f"{safe_title}{ext_map[fmt]}"
        file_path = os.path.join(d_dir, filename)

        # Path-traversal check
        if not os.path.abspath(file_path).startswith(os.path.abspath(self.outputs_dir)):
            return {"error": {"code": "DELIVERABLE_SAVE_FAILED", "message": "Path traversal detected."}}

        try:
            if fmt == "DOCX":
                self._generate_docx(file_path, title, content)
            elif fmt == "PDF":
                self._generate_pdf(file_path, title, content)
            elif fmt == "PPTX":
                self._generate_pptx(file_path, title, content)
            elif fmt == "XLSX":
                self._generate_xlsx(file_path, title, content)
        except Exception as e:
            logger.error(f"Deliverable generation failed: {e}")
            return {"error": {"code": "DELIVERABLE_GENERATION_FAILED", "message": str(e)}}

        if not os.path.exists(file_path):
            return {"error": {"code": "DELIVERABLE_SAVE_FAILED", "message": "File was not created."}}

        size = os.path.getsize(file_path)
        now = self._now()
        meta = {
            "deliverable_id": deliverable_id,
            "project_id": project_id,
            "task_id": task_id,
            "approval_id": approval_id,
            "type": fmt,
            "filename": filename,
            "path": file_path,
            "created_at": now,
            "size": size,
            "status": "ready",
        }
        self._save_meta(meta)
        logger.info(f"Deliverable created: {deliverable_id} ({fmt}) for project {project_id}")
        return meta

    def register_file(self, project_id: str, title: str, source_path: str, task_id: Optional[str] = None) -> dict:
        """Registers an already generated file (e.g. a Tuffy approval DOCX) as a project deliverable."""
        ext = os.path.splitext(source_path)[1].lower()
        fmt = {".docx": "DOCX", ".pdf": "PDF", ".pptx": "PPTX", ".xlsx": "XLSX"}.get(ext)
        if not fmt:
            return {"error": {"code": "UNSUPPORTED_FORMAT", "message": f"Unsupported deliverable file type '{ext}'."}}
        if not os.path.exists(source_path):
            return {"error": {"code": "DELIVERABLE_FILE_MISSING", "message": "Generated file not found on disk."}}
        if not os.path.abspath(source_path).startswith(os.path.abspath(settings.storage_root)):
            return {"error": {"code": "DELIVERABLE_ACCESS_DENIED", "message": "Source file is outside approved storage."}}

        deliverable_id = f"dlvr_{uuid.uuid4().hex[:12]}"
        d_dir = self._deliverable_dir(project_id, deliverable_id)
        os.makedirs(d_dir, exist_ok=True)
        filename = f"{_safe_filename(title)}{ext}"
        file_path = os.path.join(d_dir, filename)
        shutil.copyfile(source_path, file_path)

        meta = {
            "deliverable_id": deliverable_id,
            "project_id": project_id,
            "task_id": task_id,
            "approval_id": None,
            "type": fmt,
            "filename": filename,
            "path": file_path,
            "created_at": self._now(),
            "size": os.path.getsize(file_path),
            "status": "ready",
        }
        self._save_meta(meta)
        return meta

    def link_approval(self, project_id: str, deliverable_id: str, approval_id: str):
        meta = self.get_deliverable(project_id, deliverable_id)
        if meta:
            meta["approval_id"] = approval_id
            self._save_meta(meta)

    def get_deliverable(self, project_id: str, deliverable_id: str) -> Optional[dict]:
        meta = self._load_meta(project_id, deliverable_id)
        if meta is None:
            return None
        # Enforce project isolation
        if meta.get("project_id") != project_id:
            return None
        return meta

    def list_deliverables(self, project_id: str) -> List[dict]:
        pd = self._project_dir(project_id)
        if not os.path.exists(pd):
            return []
        results = []
        for dname in os.listdir(pd):
            meta = self._load_meta(project_id, dname)
            if meta and meta.get("project_id") == project_id:
                results.append(meta)
        return results

    def get_file_path(self, project_id: str, deliverable_id: str) -> dict:
        meta = self.get_deliverable(project_id, deliverable_id)
        if meta is None:
            return {"error": {"code": "DELIVERABLE_NOT_FOUND", "message": "Deliverable not found."}}
        path = meta.get("path", "")
        if not os.path.exists(path):
            return {"error": {"code": "DELIVERABLE_FILE_MISSING", "message": "File not found on disk."}}
        # Extra path-traversal guard on download
        if not os.path.abspath(path).startswith(os.path.abspath(self.outputs_dir)):
            return {"error": {"code": "DELIVERABLE_ACCESS_DENIED", "message": "Path traversal denied."}}
        return {"file_path": path, "filename": meta.get("filename")}


deliverable_service = DeliverableService()
