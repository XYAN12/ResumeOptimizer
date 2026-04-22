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


def test_full_agent_flow_requires_confirmation() -> None:
    agent = build_agent()
    resume_text = """
    Alex Chen
    alex@example.com
    Experience
    Backend Engineer at Example Corp
    Built FastAPI services and PostgreSQL APIs
    Skills
    Python, FastAPI, PostgreSQL, Docker
    """
    jd_text = """
    Senior Backend Engineer
    - Required: Python
    - Required: FastAPI
    - Preferred: AWS
    - Build scalable APIs
    """

    analysis = agent.analyze(resume_text, jd_text)
    assert analysis.approval_required is True
    assert analysis.analysis.fact_constraints

    rewrite = agent.generate_rewrite(analysis.session_id, True)
    assert "FastAPI" in rewrite.rewrite.markdown


def test_export_after_rewrite() -> None:
    agent = build_agent()
    analysis = agent.analyze(
        "Taylor\nExperience\nDeveloper at Foo\nSkills\nPython, React",
        "Frontend Engineer\n- Required: React",
    )
    agent.generate_rewrite(analysis.session_id, True)
    exported = agent.export(analysis.session_id, "md")
    assert exported.filename.endswith(".md")
    assert exported.content_base64
