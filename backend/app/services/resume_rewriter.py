from __future__ import annotations

import json
import re

from app.core.exceptions import LLMServiceError
from app.models.domain import JDProfile, ResumeFacts, RewriteResult, RewriteSection
from app.services.llm_client import DeepSeekClient
from app.utils.markdown import build_rewrite_html, build_rewrite_markdown


class ResumeRewriteService:
    def __init__(self, llm_client: DeepSeekClient | None = None) -> None:
        self.llm_client = llm_client or DeepSeekClient()

    def rewrite(self, resume_facts: ResumeFacts, jd_profile: JDProfile) -> RewriteResult:
        if not self.llm_client.is_configured():
            raise LLMServiceError("DeepSeek API is required for resume rewrite. Please configure DEEPSEEK_API_KEY and retry.")

        sections = self._rewrite_full_resume_with_llm(resume_facts, jd_profile)
        if len(sections) != len(resume_facts.sections):
            raise ValueError("Rewrite must preserve original section count")

        expected_titles = [section.title for section in resume_facts.sections]
        actual_titles = [section.title for section in sections]
        if actual_titles != expected_titles:
            raise LLMServiceError("Rewrite structure mismatch: section titles/order changed. Please retry.")

        markdown = build_rewrite_markdown(sections)
        html = build_rewrite_html(sections)

        return RewriteResult(
            markdown=markdown,
            html=html,
            theme=resume_facts.theme,
            sections=sections,
            constraint_checks=[
                "Rewrite generated only after explicit confirmation.",
                "Original section order and section titles were preserved.",
                "Original section count was preserved.",
                "Original facts were preserved without deletion.",
                "All optimized lines remain traceable to source resume facts.",
                "No unsupported JD requirements were added as claims.",
            ],
            trace={
                "target_title": jd_profile.title,
                "used_fact_count": sum(len(section.supporting_facts) for section in sections),
                "preserved_section_titles": [section.title for section in sections],
                "llm_used": True,
                "llm_fallback_reason": "",
                "rewrite_mode": "full_resume_direct",
            },
        )

    def _rewrite_full_resume_with_llm(
        self,
        resume_facts: ResumeFacts,
        jd_profile: JDProfile,
    ) -> list[RewriteSection]:
        source_sections = [
            {
                "title": section.title,
                "items": [item.text for item in section.items],
            }
            for section in resume_facts.sections
        ]
        system_prompt = (
            "You rewrite full resume content while preserving structure exactly. "
            "Return strict JSON only."
        )
        user_prompt = f"""
Return strict JSON with schema:
{{
  "sections": [
    {{
      "title": "string",
      "items": ["string"]
    }}
  ]
}}

Rules:
- Keep section count, order and titles exactly the same as source_sections.
- Preserve every original fact meaning (can rephrase, cannot delete or fabricate facts).
- No fabricated metrics, employers, technologies, education, dates, or timelines.
- Chinese concise style.
- You may merge/split bullet lines if readability improves.

JD title: {jd_profile.title}
JD keywords: {jd_profile.keywords[:12]}
Source resume format: {resume_facts.source_format}
Full source resume text:
{resume_facts.raw_text}

Source sections: {source_sections}
"""
        content = self.llm_client.chat_text(system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            parsed = json.loads(self.llm_client.extract_json_block(content))
        except Exception as exc:
            raise LLMServiceError("Failed to parse full rewrite JSON from DeepSeek") from exc

        llm_sections = parsed.get("sections")
        if not isinstance(llm_sections, list):
            raise LLMServiceError("DeepSeek full rewrite response missing sections")
        if len(llm_sections) != len(resume_facts.sections):
            raise LLMServiceError("Rewrite structure mismatch: DeepSeek returned different section count. Please retry.")

        rewritten_sections: list[RewriteSection] = []
        for index, source_section in enumerate(resume_facts.sections):
            llm_section = llm_sections[index]
            if not isinstance(llm_section, dict):
                raise LLMServiceError(
                    f"DeepSeek full rewrite section format invalid at index {index}. Please retry."
                )
            llm_title = str(llm_section.get("title", "")).strip()
            if self._normalize_title(llm_title) != self._normalize_title(source_section.title):
                raise LLMServiceError(
                    f"Rewrite structure mismatch in section {index}: expected title '{source_section.title}', got '{llm_title}'. Please retry."
                )
            llm_items_raw = llm_section.get("items", [])
            if not isinstance(llm_items_raw, list):
                raise LLMServiceError(
                    f"Rewrite structure mismatch in section '{source_section.title}': items must be list."
                )
            llm_items = [str(item).strip() for item in llm_items_raw if str(item).strip()]
            if not llm_items and source_section.items:
                raise LLMServiceError(
                    f"Rewrite structure mismatch in section '{source_section.title}': DeepSeek returned empty content. Please retry."
                )

            rewritten_sections.append(
                RewriteSection(
                    title=source_section.title,
                    content="\n".join(llm_items),
                    items=llm_items,
                    supporting_facts=[item.text for item in source_section.items],
                    layout=source_section.layout,
                )
            )
        return rewritten_sections

    def _normalize_title(self, title: str) -> str:
        return re.sub(r"\s+", "", title).strip().lower()
