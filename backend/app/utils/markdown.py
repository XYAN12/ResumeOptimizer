from __future__ import annotations

from app.models.domain import ResumeFacts, RewriteSection


def build_rewrite_markdown(
    name_line: str,
    target_title: str,
    summary: str,
    sections: list[RewriteSection],
) -> str:
    parts = [f"# {name_line}".strip()]
    if target_title:
        parts.append(f"> Optimized for: {target_title}")
    if summary:
        parts.append("## Professional Summary")
        parts.append(summary)

    for section in sections:
        parts.append(f"## {section.title}")
        parts.append(section.content.strip())

    return "\n\n".join(part for part in parts if part.strip()) + "\n"


def guess_name_line(facts: ResumeFacts) -> str:
    if facts.contact:
        return facts.contact[0].text
    return "Candidate"
