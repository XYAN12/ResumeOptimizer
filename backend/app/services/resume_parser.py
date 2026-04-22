from __future__ import annotations

import re
from collections import defaultdict

from app.models.domain import ResumeFact, ResumeFacts


SECTION_HINTS = {
    "experience": ["experience", "work experience", "employment", "professional experience"],
    "projects": ["projects", "project experience"],
    "education": ["education"],
    "skills": ["skills", "technical skills", "technologies"],
    "achievements": ["awards", "achievements", "certifications"],
}


class ResumeParserService:
    def parse(self, raw_text: str) -> ResumeFacts:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        buckets: dict[str, list[ResumeFact]] = defaultdict(list)
        current_section = "other"

        for line in lines:
            section = self._match_section(line)
            if section:
                current_section = section
                continue

            fact = ResumeFact(
                category=current_section,
                text=line,
                evidence=line,
            )
            buckets[current_section].append(fact)

        if lines:
            buckets["contact"].extend(
                ResumeFact(category="contact", text=line, evidence=line)
                for line in lines[: min(3, len(lines))]
            )

        summary = self._build_summary(lines)
        return ResumeFacts(
            raw_text=raw_text.strip(),
            summary=summary,
            contact=buckets["contact"],
            experience=buckets["experience"],
            projects=buckets["projects"],
            education=buckets["education"],
            skills=self._extract_skills(lines, buckets["skills"]),
            achievements=buckets["achievements"],
            other=buckets["other"],
        )

    def _match_section(self, line: str) -> str | None:
        normalized = re.sub(r"[^a-z ]", "", line.lower()).strip()
        for section, hints in SECTION_HINTS.items():
            if normalized in hints:
                return section
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
