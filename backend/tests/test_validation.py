import pytest

from app.core.exceptions import ValidationError
from app.services.agent.memory import AgentMemoryStore
from app.services.agent.orchestrator import ResumeOptimizerAgent
from app.services.export_service import ExportService
from app.services.gap_analysis import GapAnalysisService
from app.services.jd_analyzer import JDAnalyzerService
from app.services.resume_parser import ResumeParserService
from app.services.resume_rewriter import ResumeRewriteService


def build_agent() -> ResumeOptimizerAgent:
    return ResumeOptimizerAgent(
        memory_store=AgentMemoryStore(),
        resume_parser=ResumeParserService(),
        jd_analyzer=JDAnalyzerService(),
        gap_analysis=GapAnalysisService(),
        resume_rewriter=ResumeRewriteService(),
        export_service=ExportService(),
    )


def test_empty_inputs_are_rejected() -> None:
    agent = build_agent()
    with pytest.raises(ValidationError):
        agent.analyze("", "jd")
    with pytest.raises(ValidationError):
        agent.analyze("resume", "")
