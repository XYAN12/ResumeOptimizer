from __future__ import annotations

import re

from app.models.domain import JDProfile


class JDAnalyzerService:
    def analyze(self, raw_text: str) -> JDProfile:
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        title = lines[0] if lines else ""
        bullets = [line.lstrip("-• ").strip() for line in lines[1:]]

        required_skills = []
        preferred_skills = []
        qualifications = []

        for bullet in bullets:
            lower = bullet.lower()
            if any(word in lower for word in ["must", "required", "proficient", "experience with"]):
                required_skills.append(bullet)
            elif any(word in lower for word in ["preferred", "nice to have", "plus"]):
                preferred_skills.append(bullet)
            elif any(word in lower for word in ["degree", "years", "qualification"]):
                qualifications.append(bullet)

        keywords = self._extract_keywords(raw_text)
        responsibilities = bullets[:8]

        return JDProfile(
            raw_text=raw_text.strip(),
            title=title,
            responsibilities=responsibilities,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            qualifications=qualifications,
            keywords=keywords,
        )

    def _extract_keywords(self, text: str) -> list[str]:
        candidates = re.findall(r"[A-Za-z][A-Za-z0-9.+#/-]{2,}", text)
        seen = set()
        keywords = []
        for token in candidates:
            lowered = token.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            keywords.append(token)
        return keywords[:20]
