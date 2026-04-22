from functools import lru_cache

from app.services.agent.memory import AgentMemoryStore
from app.services.agent.orchestrator import ResumeOptimizerAgent
from app.services.export_service import ExportService
from app.services.gap_analysis import GapAnalysisService
from app.services.jd_analyzer import JDAnalyzerService
from app.services.resume_parser import ResumeParserService
from app.services.resume_rewriter import ResumeRewriteService


@lru_cache
def get_agent() -> ResumeOptimizerAgent:
    return ResumeOptimizerAgent(
        memory_store=AgentMemoryStore(),
        resume_parser=ResumeParserService(),
        jd_analyzer=JDAnalyzerService(),
        gap_analysis=GapAnalysisService(),
        resume_rewriter=ResumeRewriteService(),
        export_service=ExportService(),
    )
