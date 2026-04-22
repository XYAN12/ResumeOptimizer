from __future__ import annotations

import json

from app.core.exceptions import LLMServiceError
from app.models.domain import AnalysisItem, GapAnalysisResult, JDProfile, ResumeFacts
from app.services.llm_client import DeepSeekClient


class GapAnalysisService:
    def __init__(self, llm_client: DeepSeekClient | None = None) -> None:
        self.llm_client = llm_client or DeepSeekClient()

    def analyze(self, resume_facts: ResumeFacts, jd_profile: JDProfile) -> GapAnalysisResult:
        if not self.llm_client.is_configured():
            raise LLMServiceError(
                "DeepSeek API is required for resume analysis. Please configure DEEPSEEK_API_KEY and retry."
            )
        return self._analyze_with_llm(resume_facts, jd_profile)

    def _analyze_with_llm(self, resume_facts: ResumeFacts, jd_profile: JDProfile) -> GapAnalysisResult:
        system_prompt = (
            "You are a resume-gap analyst. "
            "Use only facts from the resume. Never invent facts."
        )
        user_prompt = f"""
Return strict JSON with schema:
{{
  "highlights": [{{"title":"string","detail":"string","supporting_facts":["string"]}}],
  "gaps": [{{"title":"string","detail":"string","supporting_facts":["string"]}}],
  "suggestions": [{{"title":"string","detail":"string","supporting_facts":["string"]}}]
}}

Rules:
- supporting_facts must come from resume facts verbatim.
- If a requirement has no support, put it in gaps only.
- Keep concise Chinese output.

JD profile:
title: {jd_profile.title}
responsibilities: {jd_profile.responsibilities}
required_skills: {jd_profile.required_skills}
preferred_skills: {jd_profile.preferred_skills}
qualifications: {jd_profile.qualifications}
keywords: {jd_profile.keywords}

Resume facts:
{resume_facts.all_fact_texts()}
"""
        content = self.llm_client.chat_text(system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            parsed = json.loads(self.llm_client.extract_json_block(content))
        except Exception as exc:
            raise LLMServiceError("Failed to parse gap analysis JSON from DeepSeek") from exc
        constraints = [
            "禁止新增未在原始简历中出现的公司、学校、项目、技术栈、奖项、时间线或量化指标。",
            "若 JD 要求在原始简历中没有事实支撑，只能标记为缺口，不可伪造补齐。",
            "最终改写必须等待用户确认后执行。",
        ]
        return GapAnalysisResult(
            highlights=self._parse_items(parsed.get("highlights")),
            gaps=self._parse_items(parsed.get("gaps")),
            suggestions=self._parse_items(parsed.get("suggestions")),
            fact_constraints=constraints,
            trace={
                "llm_used": True,
                "resume_fact_count": len(resume_facts.all_fact_texts()),
                "jd_keyword_count": len(jd_profile.keywords),
            },
        )

    def _parse_items(self, raw_items) -> list[AnalysisItem]:
        if not isinstance(raw_items, list):
            return []
        items: list[AnalysisItem] = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            items.append(
                AnalysisItem(
                    title=str(item.get("title", "")).strip() or "未命名项",
                    detail=str(item.get("detail", "")).strip(),
                    supporting_facts=[
                        str(fact).strip()
                        for fact in item.get("supporting_facts", [])
                        if str(fact).strip()
                    ],
                )
            )
        return items
