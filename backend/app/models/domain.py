from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FactSource(str, Enum):
    RESUME = "resume"
    INFERRED = "inferred"


class ResumeFact(BaseModel):
    category: str
    text: str
    source: FactSource = FactSource.RESUME
    evidence: Optional[str] = None


class ResumeFacts(BaseModel):
    raw_text: str
    summary: str = ""
    contact: List[ResumeFact] = Field(default_factory=list)
    experience: List[ResumeFact] = Field(default_factory=list)
    projects: List[ResumeFact] = Field(default_factory=list)
    education: List[ResumeFact] = Field(default_factory=list)
    skills: List[ResumeFact] = Field(default_factory=list)
    achievements: List[ResumeFact] = Field(default_factory=list)
    other: List[ResumeFact] = Field(default_factory=list)

    def all_fact_texts(self) -> List[str]:
        groups = [
            self.contact,
            self.experience,
            self.projects,
            self.education,
            self.skills,
            self.achievements,
            self.other,
        ]
        return [fact.text for group in groups for fact in group]


class JDProfile(BaseModel):
    raw_text: str
    title: str = ""
    responsibilities: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class AnalysisItem(BaseModel):
    title: str
    detail: str
    supporting_facts: List[str] = Field(default_factory=list)


class GapAnalysisResult(BaseModel):
    highlights: List[AnalysisItem] = Field(default_factory=list)
    gaps: List[AnalysisItem] = Field(default_factory=list)
    suggestions: List[AnalysisItem] = Field(default_factory=list)
    fact_constraints: List[str] = Field(default_factory=list)
    trace: Dict[str, Any] = Field(default_factory=dict)


class RewriteSection(BaseModel):
    title: str
    content: str
    supporting_facts: List[str] = Field(default_factory=list)


class RewriteResult(BaseModel):
    markdown: str
    sections: List[RewriteSection] = Field(default_factory=list)
    constraint_checks: List[str] = Field(default_factory=list)
    trace: Dict[str, Any] = Field(default_factory=dict)


class AgentState(BaseModel):
    resume_text: str
    jd_text: str
    resume_facts: ResumeFacts
    jd_profile: JDProfile
    analysis: GapAnalysisResult
    rewrite: RewriteResult | None = None
    approval_required: bool = True
