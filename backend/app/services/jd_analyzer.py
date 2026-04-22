from __future__ import annotations

import json

from app.core.exceptions import LLMServiceError
from app.models.domain import JDProfile
from app.services.llm_client import DeepSeekClient


class JDAnalyzerService:
    def __init__(self, llm_client: DeepSeekClient | None = None) -> None:
        self.llm_client = llm_client or DeepSeekClient()

    def analyze(self, raw_text: str) -> JDProfile:
        if not self.llm_client.is_configured():
            raise LLMServiceError(
                "DeepSeek API is required for resume analysis. Please configure DEEPSEEK_API_KEY and retry."
            )
        return self._analyze_with_llm(raw_text)

    def _analyze_with_llm(self, raw_text: str) -> JDProfile:
        system_prompt = (
            "You are an expert recruiter assistant. "
            "Extract a structured JD profile and return strict JSON only."
        )
        user_prompt = f"""
Return JSON with this exact schema:
{{
  "title": "string",
  "responsibilities": ["string"],
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "qualifications": ["string"],
  "keywords": ["string"]
}}

JD:
{raw_text}
"""
        content = self.llm_client.chat_text(system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            parsed = json.loads(self.llm_client.extract_json_block(content))
        except Exception as exc:
            raise LLMServiceError("Failed to parse JD JSON from DeepSeek") from exc
        return JDProfile(
            raw_text=raw_text.strip(),
            title=str(parsed.get("title", "")).strip(),
            responsibilities=self._as_str_list(parsed.get("responsibilities")),
            required_skills=self._as_str_list(parsed.get("required_skills")),
            preferred_skills=self._as_str_list(parsed.get("preferred_skills")),
            qualifications=self._as_str_list(parsed.get("qualifications")),
            keywords=self._as_str_list(parsed.get("keywords"))[:20],
        )

    def _as_str_list(self, value) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]
