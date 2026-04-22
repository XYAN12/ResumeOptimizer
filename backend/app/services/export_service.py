from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from docx import Document
from markdown import markdown
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from app.core.config import get_settings
from app.core.exceptions import ExportError


class ExportService:
    def export(self, session_id: str, markdown_text: str, export_format: str) -> tuple[str, str]:
        filename = f"optimized_resume_{session_id}.{export_format}"
        if export_format == "md":
            payload = markdown_text.encode("utf-8")
        elif export_format == "docx":
            payload = self._to_docx(markdown_text)
        elif export_format == "pdf":
            payload = self._to_pdf(markdown_text)
        else:
            raise ExportError(f"Unsupported export format: {export_format}")

        settings = get_settings()
        export_dir = Path(settings.export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        (export_dir / filename).write_bytes(payload)
        return filename, base64.b64encode(payload).decode("utf-8")

    def _to_docx(self, markdown_text: str) -> bytes:
        document = Document()
        for block in markdown_text.split("\n\n"):
            line = block.strip()
            if not line:
                continue
            if line.startswith("# "):
                document.add_heading(line[2:], level=1)
            elif line.startswith("## "):
                document.add_heading(line[3:], level=2)
            else:
                document.add_paragraph(line.replace("\n", "\n"))
        buffer = BytesIO()
        document.save(buffer)
        return buffer.getvalue()

    def _to_pdf(self, markdown_text: str) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 50
        font_name = "Helvetica"
        font_size = 11
        pdf.setFont(font_name, font_size)

        plain_text = markdown(markdown_text).replace("<h1>", "").replace("</h1>", "")
        plain_text = (
            plain_text.replace("<h2>", "")
            .replace("</h2>", "")
            .replace("<p>", "")
            .replace("</p>", "\n")
            .replace("<ul>", "")
            .replace("</ul>", "")
            .replace("<li>", "- ")
            .replace("</li>", "\n")
        )

        for raw_line in plain_text.splitlines():
            line = raw_line.strip()
            if not line:
                y -= 8
                continue
            wrapped = self._wrap_line(line, width - 100, font_name, font_size)
            for part in wrapped:
                pdf.drawString(50, y, part)
                y -= 16
                if y < 60:
                    pdf.showPage()
                    pdf.setFont(font_name, font_size)
                    y = height - 50
        pdf.save()
        return buffer.getvalue()

    def _wrap_line(self, text: str, max_width: float, font_name: str, font_size: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [text]
