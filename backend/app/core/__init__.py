"""Core business logic modules."""

from app.core.errors import (
    ConnectionError,
    ConnectionPoolExhaustedError,
    ConstraintViolationError,
    CorruptDownloadError,
    # Database errors
    DatabaseError,
    # Download errors
    DownloadError,
    ElementNotFoundError,
    # Error categories
    ErrorCategory,
    ErrorSeverity,
    ExceedsAccreditedError,
    # Failed items queue
    FailedItem,
    FailedItemsQueue,
    FileNotAvailableError,
    HTTPError,
    # Base exception
    INECAgentError,
    LowConfidenceError,
    # Retry errors
    MaxRetriesExceededError,
    MissingFieldError,
    NavigationError,
    NegativeValueError,
    # Network errors
    NetworkError,
    # OCR errors
    OCRError,
    # Parsing errors
    ParsingError,
    # Portal errors
    PortalError,
    TimeoutError,
    UnreadableImageError,
    UnrecognizedFormatError,
    # Validation errors
    ValidationError,
    VoteSumMismatchError,
    # Utilities
    categorize_error,
    get_failed_items_queue,
    with_retry,
)
from app.core.logging import (
    LOGGING_CONFIG,
    JSONFormatter,
    TextFormatter,
    configure_logging,
    get_logger,
)

__all__ = [
    # Logging
    "configure_logging",
    "get_logger",
    "JSONFormatter",
    "TextFormatter",
    "LOGGING_CONFIG",
    # Error categories
    "ErrorCategory",
    "ErrorSeverity",
    # Exceptions
    "INECAgentError",
    "NetworkError",
    "ConnectionError",
    "TimeoutError",
    "HTTPError",
    "PortalError",
    "ElementNotFoundError",
    "NavigationError",
    "DownloadError",
    "FileNotAvailableError",
    "CorruptDownloadError",
    "OCRError",
    "UnreadableImageError",
    "LowConfidenceError",
    "ParsingError",
    "UnrecognizedFormatError",
    "MissingFieldError",
    "ValidationError",
    "VoteSumMismatchError",
    "NegativeValueError",
    "ExceedsAccreditedError",
    "DatabaseError",
    "ConnectionPoolExhaustedError",
    "ConstraintViolationError",
    "MaxRetriesExceededError",
    # Failed items
    "FailedItem",
    "FailedItemsQueue",
    "get_failed_items_queue",
    # Utilities
    "categorize_error",
    "with_retry",
]
