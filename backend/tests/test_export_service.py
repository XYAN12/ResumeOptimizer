from app.services.export_service import ExportService


def test_export_service_supports_all_formats() -> None:
    service = ExportService()
    markdown_text = "# Test\n\n## Experience\n\n- Did work"

    for export_format in ["md", "docx", "pdf"]:
        filename, payload = service.export("session", markdown_text, export_format)
        assert filename.endswith(f".{export_format}")
        assert payload
