"""Core business logic modules."""

from app.core.logging import (
    configure_logging,
    get_logger,
    JSONFormatter,
    TextFormatter,
    LOGGING_CONFIG,
)
from app.core.errors import (
    # Error categories
    ErrorCategory,
    ErrorSeverity,
    # Base exception
    INECAgentError,
    # Network errors
    NetworkError,
    ConnectionError,
    TimeoutError,
    HTTPError,
    # Portal errors
    PortalError,
    ElementNotFoundError,
    NavigationError,
    # Download errors
    DownloadError,
    FileNotAvailableError,
    CorruptDownloadError,
    # OCR errors
    OCRError,
    UnreadableImageError,
    LowConfidenceError,
    # Parsing errors
    ParsingError,
    UnrecognizedFormatError,
    MissingFieldError,
    # Validation errors
    ValidationError,
    VoteSumMismatchError,
    NegativeValueError,
    ExceedsAccreditedError,
    # Database errors
    DatabaseError,
    ConnectionPoolExhaustedError,
    ConstraintViolationError,
    # Retry errors
    MaxRetriesExceededError,
    # Failed items queue
    FailedItem,
    FailedItemsQueue,
    get_failed_items_queue,
    # Utilities
    categorize_error,
    with_retry,
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
