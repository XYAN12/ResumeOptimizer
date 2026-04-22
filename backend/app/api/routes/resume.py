from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import get_agent
from app.core.config import get_settings
from app.core.exceptions import FileExtractionError, ResumeOptimizerError, ValidationError
from app.models.dto import (
    AnalyzeResumeResponse,
    AnalyzeResumeTextRequest,
    ExportRequest,
    ExportResponse,
    GenerateRewriteRequest,
    GenerateRewriteResponse,
)
from app.services.agent.orchestrator import ResumeOptimizerAgent
from app.services.file_extractors import extract_resume_document

router = APIRouter(prefix="/resume", tags=["resume"])


def _raise_http_error(exc: Exception) -> None:
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, FileExtractionError):
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if isinstance(exc, ResumeOptimizerError):
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail="Unexpected server error") from exc


@router.post("/analyze-text", response_model=AnalyzeResumeResponse)
def analyze_resume_text(
    payload: AnalyzeResumeTextRequest,
    agent: ResumeOptimizerAgent = Depends(get_agent),
) -> AnalyzeResumeResponse:
    try:
        return agent.analyze(payload.resume_text or "", payload.jd_text)
    except Exception as exc:  # pragma: no cover - FastAPI boundary
        _raise_http_error(exc)


@router.post("/analyze-file", response_model=AnalyzeResumeResponse)
async def analyze_resume_file(
    jd_text: str = Form(...),
    file: UploadFile = File(...),
    agent: ResumeOptimizerAgent = Depends(get_agent),
) -> AnalyzeResumeResponse:
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(settings.allowed_extensions)}",
        )

    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Uploaded file exceeds size limit")

    try:
        extracted_document = extract_resume_document(file.filename or "resume", content)
        return agent.analyze(extracted_document.text, jd_text, extracted_document=extracted_document)
    except Exception as exc:  # pragma: no cover - FastAPI boundary
        _raise_http_error(exc)


@router.post("/rewrite", response_model=GenerateRewriteResponse)
def generate_rewrite(
    payload: GenerateRewriteRequest,
    agent: ResumeOptimizerAgent = Depends(get_agent),
) -> GenerateRewriteResponse:
    try:
        return agent.generate_rewrite(payload.session_id, payload.confirmed)
    except Exception as exc:  # pragma: no cover - FastAPI boundary
        _raise_http_error(exc)


@router.post("/export", response_model=ExportResponse)
def export_rewrite(
    payload: ExportRequest,
    agent: ResumeOptimizerAgent = Depends(get_agent),
) -> ExportResponse:
    try:
        return agent.export(payload.session_id, payload.format)
    except Exception as exc:  # pragma: no cover - FastAPI boundary
        _raise_http_error(exc)
