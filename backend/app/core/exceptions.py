class ResumeOptimizerError(Exception):
    """Base application error."""


class ValidationError(ResumeOptimizerError):
    """Raised when user input is invalid."""


class FileExtractionError(ResumeOptimizerError):
    """Raised when uploaded resume cannot be parsed."""


class LLMServiceError(ResumeOptimizerError):
    """Raised when LLM integration fails."""


class ExportError(ResumeOptimizerError):
    """Raised when export generation fails."""
