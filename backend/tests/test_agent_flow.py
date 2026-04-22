import ast
import json
import re

from app.services.agent.memory import AgentMemoryStore
from app.services.agent.orchestrator import ResumeOptimizerAgent
from app.services.export_service import ExportService
from app.services.gap_analysis import GapAnalysisService
from app.services.jd_analyzer import JDAnalyzerService
from app.services.llm_client import DeepSeekClient
from app.services.resume_parser import ResumeParserService
from app.services.resume_rewriter import ResumeRewriteService


class StrictMockLLMClient(DeepSeekClient):
    def is_configured(self) -> bool:
        return True

    def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        if "Extract a structured JD profile" in system_prompt:
            first_line = next((line.strip() for line in user_prompt.splitlines() if line.strip()), "JD")
            return json.dumps(
                {
                    "title": first_line,
                    "responsibilities": ["Build scalable APIs"],
                    "required_skills": ["Python", "FastAPI"],
                    "preferred_skills": ["AWS"],
                    "qualifications": ["3+ years backend experience"],
                    "keywords": ["Python", "FastAPI", "APIs"],
                },
                ensure_ascii=False,
            )

        if "resume-gap analyst" in system_prompt:
            resume_facts_match = re.search(r"Resume facts:\s*(\[.*\])", user_prompt, flags=re.DOTALL)
            supporting = []
            if resume_facts_match:
                supporting = ast.literal_eval(resume_facts_match.group(1))[:2]
            return json.dumps(
                {
                    "highlights": [
                        {
                            "title": "关键词匹配",
                            "detail": "简历已有关键技术栈",
                            "supporting_facts": supporting,
                        }
                    ],
                    "gaps": [{"title": "云平台经验", "detail": "缺少显式云平台项目经历", "supporting_facts": []}],
                    "suggestions": [
                        {
                            "title": "优化表达",
                            "detail": "把已有经验改写为更贴合 JD 的语境",
                            "supporting_facts": supporting,
                        }
                    ],
                },
                ensure_ascii=False,
            )

        match = re.search(r"Source sections:\s*(\[.*\])", user_prompt, flags=re.DOTALL)
        source_sections = ast.literal_eval(match.group(1)) if match else []
        rewritten_sections = []
        for section in source_sections:
            rewritten_sections.append(
                {
                    "title": section.get("title", ""),
                    "items": [f"{item}" for item in section.get("items", [])],
                }
            )
        return json.dumps({"sections": rewritten_sections}, ensure_ascii=False)

    def extract_json_block(self, content: str) -> str:
        return content


def build_agent() -> ResumeOptimizerAgent:
    mock_llm = StrictMockLLMClient()
    return ResumeOptimizerAgent(
        memory_store=AgentMemoryStore(),
        resume_parser=ResumeParserService(),
        jd_analyzer=JDAnalyzerService(llm_client=mock_llm),
        gap_analysis=GapAnalysisService(llm_client=mock_llm),
        resume_rewriter=ResumeRewriteService(llm_client=mock_llm),
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
    assert rewrite.rewrite.sections[1].title == "Experience"
    assert rewrite.rewrite.sections[2].title == "Skills"


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


def test_rewrite_preserves_original_section_order_and_full_content() -> None:
    agent = build_agent()
    resume_text = """
    张三
    zhangsan@example.com
    项目经历
    电商后台重构，负责订单模块拆分
    优化接口响应时间并补充监控告警
    教育经历
    XX大学 计算机科学与技术
    """
    jd_text = """
    后端工程师
    - 负责高并发服务开发
    - 有监控和性能优化经验
    """

    analysis = agent.analyze(resume_text, jd_text)
    rewrite = agent.generate_rewrite(analysis.session_id, True)

    assert [section.title for section in rewrite.rewrite.sections] == ["Header", "项目经历", "教育经历"]
    project_section = rewrite.rewrite.sections[1]
    assert "电商后台重构，负责订单模块拆分" in project_section.items
    assert "优化接口响应时间并补充监控告警" in project_section.items
    assert rewrite.rewrite.html
