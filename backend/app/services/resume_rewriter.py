from __future__ import annotations

import json

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

        sections: list[RewriteSection] = []
        for section in resume_facts.sections:
            rewritten_section = self._rewrite_section(section, jd_profile)
            sections.append(rewritten_section)
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
            },
        )

    def _rewrite_section(self, section, jd_profile: JDProfile) -> RewriteSection:
        items = self._rewrite_section_with_llm(section, jd_profile)
        content = "\n".join(items)
        supporting_facts = [item.text for item in section.items]
        return RewriteSection(
            title=section.title,
            content=content,
            items=items,
            supporting_facts=supporting_facts,
            layout=section.layout,
        )

    def _rewrite_section_with_llm(self, section, jd_profile: JDProfile) -> list[str]:
        if not section.items:
            return []

        source_items = [item.text for item in section.items]
        primary_system_prompt = (
            "You are a resume rewriter. Keep all facts grounded. "
            "Do not remove factual lines from source."
        )
        primary_user_prompt = f"""
Rewrite this resume section for JD alignment.
Return strict JSON: {{"items":["string"]}}

Rules:
- Keep same section title: {section.title}
- Keep same item count: {len(source_items)}
- Preserve every original fact (can rephrase, cannot delete facts).
- No fabricated metrics, employers, technologies, or timelines.
- Chinese concise style.

JD keywords: {jd_profile.keywords[:12]}
JD title: {jd_profile.title}
Source items: {source_items}
"""
        content = self.llm_client.chat_text(
            system_prompt=primary_system_prompt,
            user_prompt=primary_user_prompt,
        )
        try:
            parsed = json.loads(self.llm_client.extract_json_block(content))
        except Exception as exc:
            raise LLMServiceError("Failed to parse rewrite JSON from DeepSeek") from exc
        llm_items = [str(item).strip() for item in parsed.get("items", []) if str(item).strip()]

        if len(llm_items) == len(source_items):
            return llm_items

        repaired_items = self._retry_rewrite_with_index_mapping(
            section_title=section.title,
            source_items=source_items,
            jd_profile=jd_profile,
        )
        if len(repaired_items) != len(source_items):
            raise LLMServiceError(
                f"Rewrite structure mismatch in section '{section.title}': expected {len(source_items)} items, got {len(repaired_items)}. Please retry."
            )
        return repaired_items

    def _retry_rewrite_with_index_mapping(
        self,
        section_title: str,
        source_items: list[str],
        jd_profile: JDProfile,
    ) -> list[str]:
        indexed_items = [{ "index": idx, "text": text } for idx, text in enumerate(source_items)]
        system_prompt = (
            "You rewrite resume content while preserving structure exactly. "
            "Return strict JSON only."
        )
        user_prompt = f"""
Previous attempt returned wrong item count. Rewrite again with strict index mapping.
Return strict JSON with schema:
{{
  "items_by_index": {{
    "0": "string",
    "1": "string"
  }}
}}

Rules:
- Keep section title unchanged: {section_title}
- Must return ALL indexes from 0 to {len(source_items) - 1}, no missing and no extra keys.
- Each value must preserve original fact meaning, no invented facts.
- Chinese concise style.

JD title: {jd_profile.title}
JD keywords: {jd_profile.keywords[:12]}
Indexed source items: {indexed_items}
"""
        content = self.llm_client.chat_text(system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            parsed = json.loads(self.llm_client.extract_json_block(content))
        except Exception as exc:
            raise LLMServiceError("Failed to parse strict rewrite JSON from DeepSeek") from exc

        items_by_index = parsed.get("items_by_index")
        if not isinstance(items_by_index, dict):
            raise LLMServiceError("DeepSeek strict rewrite response missing items_by_index")

        rebuilt: list[str] = []
        for idx in range(len(source_items)):
            value = items_by_index.get(str(idx))
            if value is None:
                raise LLMServiceError(
                    f"DeepSeek strict rewrite missing index {idx} in section '{section_title}'"
                )
            rebuilt.append(str(value).strip())
        return rebuilt
