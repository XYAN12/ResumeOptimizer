from __future__ import annotations

from html import escape

from app.models.domain import ResumeFacts, RewriteSection


def build_rewrite_markdown(
    sections: list[RewriteSection],
) -> str:
    parts: list[str] = []

    for section in sections:
        if section.title.lower() == "header":
            parts.append(section.content.strip())
            continue

        parts.append(f"## {section.title}")
        if section.items:
            parts.extend(f"- {item}" for item in section.items)
        elif section.content.strip():
            parts.append(section.content.strip())

    return "\n\n".join(part for part in parts if part.strip()) + "\n"


def build_rewrite_html(sections: list[RewriteSection]) -> str:
    html_parts = ['<article class="resume-document">']
    for section in sections:
        if section.title.lower() == "header":
            header_lines = [f"<p>{escape(item)}</p>" for item in section.items]
            html_parts.append('<header class="resume-header">')
            html_parts.extend(header_lines)
            html_parts.append("</header>")
            continue

        html_parts.append('<section class="resume-section">')
        html_parts.append(f"<h2>{escape(section.title)}</h2>")
        html_parts.append("<ul>")
        html_parts.extend(f"<li>{escape(item)}</li>" for item in section.items)
        html_parts.append("</ul>")
        html_parts.append("</section>")
    html_parts.append("</article>")
    return "".join(html_parts)


def guess_name_line(facts: ResumeFacts) -> str:
    if facts.contact:
        return facts.contact[0].text
    return "Candidate"
