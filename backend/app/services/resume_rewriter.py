from __future__ import annotations

from app.models.domain import JDProfile, ResumeFacts, RewriteResult, RewriteSection
from app.utils.markdown import build_rewrite_markdown, guess_name_line


class ResumeRewriteService:
    def rewrite(self, resume_facts: ResumeFacts, jd_profile: JDProfile) -> RewriteResult:
        sections: list[RewriteSection] = []

        summary = self._build_summary(resume_facts, jd_profile)

        if resume_facts.skills:
            sections.append(
                RewriteSection(
                    title="Core Skills",
                    content="\n".join(f"- {fact.text}" for fact in resume_facts.skills[:8]),
                    supporting_facts=[fact.text for fact in resume_facts.skills[:8]],
                )
            )

        if resume_facts.experience:
            sections.append(
                RewriteSection(
                    title="Relevant Experience",
                    content="\n".join(f"- {fact.text}" for fact in resume_facts.experience[:8]),
                    supporting_facts=[fact.text for fact in resume_facts.experience[:8]],
                )
            )

        if resume_facts.projects:
            sections.append(
                RewriteSection(
                    title="Selected Projects",
                    content="\n".join(f"- {fact.text}" for fact in resume_facts.projects[:6]),
                    supporting_facts=[fact.text for fact in resume_facts.projects[:6]],
                )
            )

        if resume_facts.education:
            sections.append(
                RewriteSection(
                    title="Education",
                    content="\n".join(f"- {fact.text}" for fact in resume_facts.education[:4]),
                    supporting_facts=[fact.text for fact in resume_facts.education[:4]],
                )
            )

        markdown = build_rewrite_markdown(
            name_line=guess_name_line(resume_facts),
            target_title=jd_profile.title,
            summary=summary,
            sections=sections,
        )

        return RewriteResult(
            markdown=markdown,
            sections=sections,
            constraint_checks=[
                "Rewrite generated only after explicit confirmation.",
                "All section bullets come directly from extracted resume facts.",
                "No unsupported JD requirements were added as claims.",
            ],
            trace={
                "target_title": jd_profile.title,
                "used_fact_count": sum(len(section.supporting_facts) for section in sections),
            },
        )

    def _build_summary(self, resume_facts: ResumeFacts, jd_profile: JDProfile) -> str:
        relevant_lines = []
        if resume_facts.summary:
            relevant_lines.append(resume_facts.summary)
        if jd_profile.title:
            relevant_lines.append(
                f"Targeting {jd_profile.title} with emphasis on experience already evidenced in the original resume."
            )
        return " ".join(relevant_lines)[:500]
