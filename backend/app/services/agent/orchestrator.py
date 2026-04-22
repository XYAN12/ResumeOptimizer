from __future__ import annotations

from app.core.exceptions import ValidationError
from app.models.domain import AgentState, ExtractedResumeDocument
from app.models.dto import AnalyzeResumeResponse, ExportResponse, GenerateRewriteResponse
from app.services.agent.memory import AgentMemoryStore
from app.services.export_service import ExportService
from app.services.gap_analysis import GapAnalysisService
from app.services.jd_analyzer import JDAnalyzerService
from app.services.resume_parser import ResumeParserService
from app.services.resume_rewriter import ResumeRewriteService


class ResumeOptimizerAgent:
    def __init__(
        self,
        memory_store: AgentMemoryStore,
        resume_parser: ResumeParserService,
        jd_analyzer: JDAnalyzerService,
        gap_analysis: GapAnalysisService,
        resume_rewriter: ResumeRewriteService,
        export_service: ExportService,
    ) -> None:
        self.memory_store = memory_store
        self.resume_parser = resume_parser
        self.jd_analyzer = jd_analyzer
        self.gap_analysis = gap_analysis
        self.resume_rewriter = resume_rewriter
        self.export_service = export_service

    def analyze(
        self,
        resume_text: str,
        jd_text: str,
        extracted_document: ExtractedResumeDocument | None = None,
    ) -> AnalyzeResumeResponse:
        if not resume_text.strip():
            raise ValidationError("Resume text cannot be empty")
        if not jd_text.strip():
            raise ValidationError("JD text cannot be empty")

        resume_facts = self.resume_parser.parse(
            resume_text,
            layout_lines=extracted_document.lines if extracted_document else None,
            theme=extracted_document.theme if extracted_document else None,
            source_format=extracted_document.source_format if extracted_document else "text",
        )
        jd_profile = self.jd_analyzer.analyze(jd_text)
        analysis = self.gap_analysis.analyze(resume_facts, jd_profile)
        state = AgentState(
            resume_text=resume_text,
            jd_text=jd_text,
            resume_facts=resume_facts,
            jd_profile=jd_profile,
            analysis=analysis,
            approval_required=True,
            original_filename=extracted_document.filename if extracted_document else None,
            original_file_content=extracted_document.content if extracted_document else None,
        )
        session_id = self.memory_store.create(state)
        return AnalyzeResumeResponse(
            session_id=session_id,
            resume_facts=resume_facts,
            analysis=analysis,
            approval_required=True,
        )

    def generate_rewrite(self, session_id: str, confirmed: bool) -> GenerateRewriteResponse:
        state = self.memory_store.get(session_id)
        if not state:
            raise ValidationError("Session not found")
        if not confirmed:
            raise ValidationError("User confirmation is required before rewrite")

        rewrite = self.resume_rewriter.rewrite(state.resume_facts, state.jd_profile)
        state.rewrite = rewrite
        state.approval_required = False
        self.memory_store.update(session_id, state)
        return GenerateRewriteResponse(session_id=session_id, rewrite=rewrite)

    def export(self, session_id: str, export_format: str) -> ExportResponse:
        state = self.memory_store.get(session_id)
        if not state:
            raise ValidationError("Session not found")
        if not state.rewrite:
            raise ValidationError("Rewrite has not been generated yet")

        filename, payload = self.export_service.export(
            session_id=session_id,
            rewrite=state.rewrite,
            export_format=export_format,
            original_file_content=state.original_file_content,
            original_filename=state.original_filename,
        )
        return ExportResponse(
            session_id=session_id,
            format=export_format,
            filename=filename,
            content_base64=payload,
        )
