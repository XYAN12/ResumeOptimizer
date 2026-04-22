from __future__ import annotations

import re
from collections import defaultdict
from statistics import mean

from app.models.domain import (
    DocumentTheme,
    LayoutLine,
    ResumeFact,
    ResumeFacts,
    ResumeSection,
    SectionLayout,
)


SECTION_HINTS = {
    "experience": [
        "experience",
        "workexperience",
        "employment",
        "professionalexperience",
        "工作经历",
        "实习经历",
    ],
    "projects": ["projects", "projectexperience", "项目经历", "项目经验"],
    "education": ["education", "教育经历", "教育背景"],
    "skills": ["skills", "technicalskills", "technologies", "技能", "专业技能", "技术栈"],
    "achievements": ["awards", "achievements", "certifications", "奖项", "获奖经历", "证书"],
}


class ResumeParserService:
    def parse(
        self,
        raw_text: str,
        layout_lines: list[LayoutLine] | None = None,
        theme: DocumentTheme | None = None,
        source_format: str = "text",
    ) -> ResumeFacts:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        buckets: dict[str, list[ResumeFact]] = defaultdict(list)
        current_section = "other"
        ordered_sections: list[ResumeSection] = []
        section_index = -1
        first_explicit_section_seen = False

        if lines:
            ordered_sections.append(
                ResumeSection(
                    title="Header",
                    category="contact",
                    items=[],
                    original_order=0,
                )
            )
            section_index = 0

        layout_lookup = self._build_layout_lookup(layout_lines or [])

        for line in lines:
            matched_section = self._match_section(
                line=line,
                layout_line=layout_lookup.get(self._normalize_for_match(line)),
                theme=theme,
                source_format=source_format,
            )
            if matched_section:
                current_section = matched_section.category
                first_explicit_section_seen = True
                ordered_sections.append(
                    ResumeSection(
                        title=matched_section.title,
                        category=matched_section.category,
                        items=[],
                        original_order=len(ordered_sections),
                    )
                )
                section_index = len(ordered_sections) - 1
                continue

            fact = ResumeFact(
                category=current_section,
                text=line,
                evidence=line,
            )
            buckets[current_section].append(fact)
            if section_index < 0:
                ordered_sections.append(
                    ResumeSection(
                        title="General",
                        category=current_section,
                        items=[fact],
                        original_order=len(ordered_sections),
                    )
                )
                section_index = len(ordered_sections) - 1
            else:
                if not first_explicit_section_seen and ordered_sections[0].category == "contact":
                    ordered_sections[0].items.append(fact)
                else:
                    ordered_sections[section_index].items.append(fact)

        if ordered_sections and ordered_sections[0].category == "contact":
            buckets["contact"] = list(ordered_sections[0].items)

        summary = self._build_summary(lines)
        sections = self._attach_layouts(
            sections=ordered_sections,
            layout_lines=layout_lines or [],
            theme=theme or DocumentTheme(source_format=source_format),
        )
        return ResumeFacts(
            raw_text=raw_text.strip(),
            summary=summary,
            source_format=source_format,
            theme=theme or DocumentTheme(source_format=source_format),
            sections=sections,
            contact=buckets["contact"],
            experience=buckets["experience"],
            projects=buckets["projects"],
            education=buckets["education"],
            skills=self._extract_skills(lines, buckets["skills"]),
            achievements=buckets["achievements"],
            other=buckets["other"],
        )

    def _match_section(
        self,
        line: str,
        layout_line: LayoutLine | None = None,
        theme: DocumentTheme | None = None,
        source_format: str = "text",
    ) -> ResumeSection | None:
        normalized = re.sub(r"[\W_]+", "", line.lower(), flags=re.UNICODE).strip()
        for section, hints in SECTION_HINTS.items():
            if normalized in hints:
                return ResumeSection(title=line.strip(), category=section)
        if self._looks_like_visual_heading(
            text=line,
            layout_line=layout_line,
            theme=theme,
            source_format=source_format,
        ):
            return ResumeSection(title=line.strip(), category="other")
        return None

    def _extract_skills(self, lines: list[str], existing: list[ResumeFact]) -> list[ResumeFact]:
        if existing:
            return existing

        skill_candidates = []
        for line in lines:
            if "," in line and len(line) < 120:
                skill_candidates.append(
                    ResumeFact(category="skills", text=line, evidence=line)
                )
        return skill_candidates

    def _build_summary(self, lines: list[str]) -> str:
        return " ".join(lines[:4])[:400]

    def _attach_layouts(
        self,
        sections: list[ResumeSection],
        layout_lines: list[LayoutLine],
        theme: DocumentTheme,
    ) -> list[ResumeSection]:
        if not layout_lines:
            return sections

        remaining_lines = list(layout_lines)
        title_lines: dict[int, LayoutLine] = {}

        for index, section in enumerate(sections):
            if section.title.lower() in {"header", "general"}:
                continue

            match = self._pop_matching_line(remaining_lines, section.title)
            if match:
                title_lines[index] = match

        for index, section in enumerate(sections):
            section.layout = self._build_section_layout(
                section_index=index,
                section=section,
                sections=sections,
                title_lines=title_lines,
                layout_lines=layout_lines,
                theme=theme,
            )
        return sections

    def _build_section_layout(
        self,
        section_index: int,
        section: ResumeSection,
        sections: list[ResumeSection],
        title_lines: dict[int, LayoutLine],
        layout_lines: list[LayoutLine],
        theme: DocumentTheme,
    ) -> SectionLayout | None:
        if section.title.lower() == "header":
            header_lines = [
                line for line in layout_lines if line.text in {item.text for item in section.items}
            ]
            if not header_lines:
                return None
            return SectionLayout(
                page_number=header_lines[0].page_number,
                x=min((line.x or 0.0) for line in header_lines),
                y_top=max((line.y or 0.0) for line in header_lines),
                y_bottom=min((line.y or 0.0) for line in header_lines) - 4,
                width=(theme.page_width or 595.0) - min((line.x or 0.0) for line in header_lines) - 40,
                body_font_name=self._most_common_font_name(header_lines) or theme.body_font_name,
                body_font_size=self._average_font_size(header_lines) or theme.body_font_size,
            )

        title_line = title_lines.get(section_index)
        if not title_line:
            return None

        next_title = None
        for next_index in range(section_index + 1, len(sections)):
            next_title = title_lines.get(next_index)
            if next_title:
                break

        body_lines = [
            line
            for line in layout_lines
            if line.page_number == title_line.page_number
            and (line.y or 0.0) < (title_line.y or 0.0)
            and (
                next_title is None
                or line.page_number != next_title.page_number
                or (line.y or 0.0) > (next_title.y or 0.0)
            )
        ]

        y_bottom = (
            (next_title.y or 0.0) + 8
            if next_title and next_title.page_number == title_line.page_number
            else 48.0
        )
        x = min(
            [value for value in [title_line.x] + [line.x for line in body_lines] if value is not None],
            default=40.0,
        )
        width = (theme.page_width or 595.0) - x - 40

        return SectionLayout(
            page_number=title_line.page_number,
            x=x,
            y_top=title_line.y or 0.0,
            y_bottom=y_bottom,
            width=width,
            title_font_name=title_line.font_name or theme.heading_font_name,
            body_font_name=self._most_common_font_name(body_lines) or theme.body_font_name,
            title_font_size=title_line.font_size or theme.heading_font_size,
            body_font_size=self._average_font_size(body_lines) or theme.body_font_size,
        )

    def _pop_matching_line(
        self,
        lines: list[LayoutLine],
        text: str,
    ) -> LayoutLine | None:
        target = self._normalize_for_match(text)
        for index, line in enumerate(lines):
            if self._normalize_for_match(line.text) == target:
                return lines.pop(index)
        return None

    def _normalize_for_match(self, text: str) -> str:
        return re.sub(r"\s+", "", text).strip().lower()

    def _build_layout_lookup(self, layout_lines: list[LayoutLine]) -> dict[str, LayoutLine]:
        lookup: dict[str, LayoutLine] = {}
        for line in layout_lines:
            key = self._normalize_for_match(line.text)
            if key not in lookup:
                lookup[key] = line
        return lookup

    def _looks_like_visual_heading(
        self,
        text: str,
        layout_line: LayoutLine | None,
        theme: DocumentTheme | None,
        source_format: str,
    ) -> bool:
        if source_format not in {"pdf", "docx"}:
            return False
        stripped = text.strip()
        if not stripped:
            return False
        if len(stripped) > 32:
            return False
        if any(ch in stripped for ch in ".;:!?，。；：、()[]{}"):
            return False
        if any(ch.isdigit() for ch in stripped):
            return False
        if stripped.startswith(("-", "•", "*")):
            return False
        if len(stripped.split()) > 5:
            return False
        if layout_line and theme and layout_line.font_size and theme.body_font_size:
            threshold = max(theme.body_font_size + 2.0, theme.body_font_size * 1.25)
            if layout_line.font_size >= threshold:
                return True
        return False

    def _most_common_font_name(self, lines: list[LayoutLine]) -> str | None:
        font_names = [line.font_name for line in lines if line.font_name]
        if not font_names:
            return None
        return max(set(font_names), key=font_names.count)

    def _average_font_size(self, lines: list[LayoutLine]) -> float | None:
        font_sizes = [line.font_size for line in lines if line.font_size]
        if not font_sizes:
            return None
        return round(mean(font_sizes), 1)
