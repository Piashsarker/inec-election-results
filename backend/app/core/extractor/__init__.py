"""Data extraction and parsing components."""

from app.core.extractor.parser import (
    ElectionDataExtractor,
    ExtractionResult,
    PartyVote,
    SummaryFields,
)
from app.core.extractor.validator import (
    DataValidator,
    ValidationError,
    ValidationErrorType,
    ValidationResult,
    ValidationSeverity,
)

__all__ = [
    # Parser
    "ElectionDataExtractor",
    "ExtractionResult",
    "PartyVote",
    "SummaryFields",
    # Validator
    "DataValidator",
    "ValidationError",
    "ValidationErrorType",
    "ValidationResult",
    "ValidationSeverity",
]
