from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

from app.models.domain import GapAnalysisResult, ResumeFacts, RewriteResult


class AnalyzeResumeResponse(BaseModel):
    session_id: str
    resume_facts: ResumeFacts
    analysis: GapAnalysisResult
    approval_required: bool = True


class AnalyzeResumeTextRequest(BaseModel):
    resume_text: Optional[str] = None
    jd_text: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_resume_text(self) -> "AnalyzeResumeTextRequest":
        if not self.resume_text or not self.resume_text.strip():
            raise ValueError("resume_text cannot be empty when not uploading a file")
        return self


class GenerateRewriteRequest(BaseModel):
    session_id: str
    confirmed: Literal[True]


class GenerateRewriteResponse(BaseModel):
    session_id: str
    rewrite: RewriteResult


class ExportRequest(BaseModel):
    session_id: str
    format: Literal["md", "docx", "pdf"]


class ExportResponse(BaseModel):
    session_id: str
    format: str
    filename: str
    content_base64: str
