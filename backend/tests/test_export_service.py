import base64

from app.services.export_service import ExportService
from app.models.domain import RewriteResult, RewriteSection


def test_export_service_supports_all_formats() -> None:
    service = ExportService()
    rewrite = RewriteResult(
        markdown="# Test\n\n## Experience\n\n- Did work",
        html="<article><section><h2>Experience</h2><ul><li>Did work</li></ul></section></article>",
        sections=[
            RewriteSection(title="Header", content="Test", items=["Test"]),
            RewriteSection(title="Experience", content="Did work", items=["Did work"]),
        ],
    )

    for export_format in ["md", "docx", "pdf"]:
        filename, payload = service.export("session", rewrite, export_format)
        assert filename.endswith(f".{export_format}")
        assert payload


def test_pdf_export_supports_chinese_content() -> None:
    service = ExportService()
    rewrite = RewriteResult(
        markdown="张三\n\n## 项目经历\n\n- 优化中文 PDF 导出",
        html="<article><header><p>张三</p></header><section><h2>项目经历</h2><ul><li>优化中文 PDF 导出</li></ul></section></article>",
        sections=[
            RewriteSection(title="Header", content="张三", items=["张三"]),
            RewriteSection(title="项目经历", content="优化中文 PDF 导出", items=["优化中文 PDF 导出"]),
        ],
    )

    filename, payload = service.export("session-cn", rewrite, "pdf")
    pdf_bytes = base64.b64decode(payload)

    assert filename.endswith(".pdf")
    assert pdf_bytes.startswith(b"%PDF")
