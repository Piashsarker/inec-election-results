"""Error handling and retry queue for INEC Election Results Agent.

This module provides:
- Error categorization (network, parsing, validation)
- Custom exception classes for different error types
- Failed items queue for retry/review
- Error context tracking

Requirements: 7.2, 7.3, 7.5
"""
from __future__ import annotations


import asyncio
import uuid
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ErrorCategory(str, Enum):
    """Error categories for classification and handling.
    
    Requirement 7.2: Categorize errors as network, parsing, or validation errors.
    """

    NETWORK = "network"
    PARSING = "parsing"
    VALIDATION = "validation"
    PORTAL = "portal"
    DOWNLOAD = "download"
    OCR = "ocr"
    DATABASE = "database"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity levels for prioritization."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Base exception classes

class INECAgentError(Exception):
    """Base exception for all INEC Agent errors."""

    category: ErrorCategory = ErrorCategory.UNKNOWN
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    retryable: bool = False

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        """Initialize error with message and context.
        
        Args:
            message: Human-readable error message
            context: Additional context data for debugging
            cause: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.cause = cause
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "retryable": self.retryable,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "cause": str(self.cause) if self.cause else None,
        }


# Network errors (Requirement 7.2, 7.3)

class NetworkError(INECAgentError):
    """Network-related errors (connection, timeout, DNS).
    
    These errors are typically retryable with exponential backoff.
    """

    category = ErrorCategory.NETWORK
    severity = ErrorSeverity.MEDIUM
    retryable = True


class ConnectionError(NetworkError):
    """Failed to establish connection."""
    pass


class TimeoutError(NetworkError):
    """Request timed out."""
    pass


class HTTPError(NetworkError):
    """HTTP error response received."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        context = context or {}
        context["status_code"] = status_code
        super().__init__(message, context=context, cause=cause)
        self.status_code = status_code

        # 5xx errors are retryable, 4xx are not
        self.retryable = 500 <= status_code < 600


# Portal errors

class PortalError(INECAgentError):
    """INEC portal navigation errors."""

    category = ErrorCategory.PORTAL
    severity = ErrorSeverity.MEDIUM
    retryable = False


class ElementNotFoundError(PortalError):
    """Expected page element not found."""
    pass


class NavigationError(PortalError):
    """Failed to navigate to expected page."""
    retryable = True


# Download errors

class DownloadError(INECAgentError):
    """Result sheet download errors."""

    category = ErrorCategory.DOWNLOAD
    severity = ErrorSeverity.MEDIUM
    retryable = True


class FileNotAvailableError(DownloadError):
    """Result sheet file not available."""
    retryable = False


class CorruptDownloadError(DownloadError):
    """Downloaded file is corrupt or invalid."""
    pass


# OCR errors

class OCRError(INECAgentError):
    """OCR processing errors."""

    category = ErrorCategory.OCR
    severity = ErrorSeverity.MEDIUM
    retryable = False


class UnreadableImageError(OCRError):
    """Image cannot be read by OCR engine."""
    pass


class LowConfidenceError(OCRError):
    """OCR confidence below threshold."""
    pass


# Parsing errors (Requirement 7.2)

class ParsingError(INECAgentError):
    """Data parsing errors."""

    category = ErrorCategory.PARSING
    severity = ErrorSeverity.MEDIUM
    retryable = False


class UnrecognizedFormatError(ParsingError):
    """Document format not recognized."""
    pass


class MissingFieldError(ParsingError):
    """Required field missing from extracted data."""

    def __init__(
        self,
        message: str,
        *,
        field_name: str,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        context = context or {}
        context["missing_field"] = field_name
        super().__init__(message, context=context, cause=cause)
        self.field_name = field_name


# Validation errors (Requirement 7.2)

class ValidationError(INECAgentError):
    """Data validation errors."""

    category = ErrorCategory.VALIDATION
    severity = ErrorSeverity.LOW
    retryable = False


class VoteSumMismatchError(ValidationError):
    """Sum of party votes doesn't match total valid votes."""

    def __init__(
        self,
        message: str,
        *,
        party_sum: int,
        valid_votes: int,
        context: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ):
        context = context or {}
        context["party_sum"] = party_sum
        context["valid_votes"] = valid_votes
        context["difference"] = abs(party_sum - valid_votes)
        super().__init__(message, context=context, cause=cause)


class NegativeValueError(ValidationError):
    """Negative value found where positive expected."""
    pass


class ExceedsAccreditedError(ValidationError):
    """Total votes exceed accredited voters."""
    pass


# Database errors

class DatabaseError(INECAgentError):
    """Database operation errors."""

    category = ErrorCategory.DATABASE
    severity = ErrorSeverity.HIGH
    retryable = True


class ConnectionPoolExhaustedError(DatabaseError):
    """Database connection pool exhausted."""
    pass


class ConstraintViolationError(DatabaseError):
    """Database constraint violation."""
    retryable = False


# Retry exceeded error

class MaxRetriesExceededError(INECAgentError):
    """Maximum retry attempts exceeded."""

    severity = ErrorSeverity.HIGH
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        max_retries: int,
        last_error: Exception | None = None,
        context: dict[str, Any] | None = None,
    ):
        context = context or {}
        context["max_retries"] = max_retries
        super().__init__(message, context=context, cause=last_error)
        self.max_retries = max_retries
        self.last_error = last_error


# Failed item tracking (Requirement 7.5)

@dataclass
class FailedItem:
    """Represents a failed processing item for retry/review.
    
    Requirement 7.5: Store failed items in a separate queue for manual review or retry.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_type: str = ""  # e.g., "polling_unit", "result_sheet", "extraction"
    item_id: str = ""  # Identifier of the failed item
    error: INECAgentError = field(default_factory=lambda: INECAgentError("Unknown error"))
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_retry_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def can_retry(self) -> bool:
        """Check if item can be retried."""
        return self.error.retryable and self.retry_count < self.max_retries

    @property
    def error_category(self) -> ErrorCategory:
        """Get error category."""
        return self.error.category

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "item_type": self.item_type,
            "item_id": self.item_id,
            "error": self.error.to_dict(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "can_retry": self.can_retry,
            "created_at": self.created_at.isoformat(),
            "last_retry_at": self.last_retry_at.isoformat() if self.last_retry_at else None,
            "metadata": self.metadata,
        }


class FailedItemsQueue:
    """Queue for managing failed items for retry/review.
    
    Provides thread-safe operations for adding, retrieving, and managing
    failed items. Items can be filtered by category, retried, or marked
    for manual review.
    
    Requirement 7.5: Store failed items in a separate queue for manual review or retry.
    """

    def __init__(self, max_size: int = 10000):
        """Initialize failed items queue.
        
        Args:
            max_size: Maximum number of items to store
        """
        self._queue: deque[FailedItem] = deque(maxlen=max_size)
        self._lock = asyncio.Lock()
        self._by_category: dict[ErrorCategory, list[FailedItem]] = {
            cat: [] for cat in ErrorCategory
        }

    async def add(
        self,
        item_type: str,
        item_id: str,
        error: INECAgentError,
        *,
        max_retries: int = 3,
        metadata: dict[str, Any] | None = None,
    ) -> FailedItem:
        """Add a failed item to the queue.
        
        Args:
            item_type: Type of item (e.g., "polling_unit")
            item_id: Identifier of the failed item
            error: The error that occurred
            max_retries: Maximum retry attempts
            metadata: Additional metadata
            
        Returns:
            Created FailedItem instance
        """
        failed_item = FailedItem(
            item_type=item_type,
            item_id=item_id,
            error=error,
            max_retries=max_retries,
            metadata=metadata or {},
        )

        async with self._lock:
            self._queue.append(failed_item)
            self._by_category[error.category].append(failed_item)

        logger.warning(
            f"Added failed item to queue: {item_type}/{item_id}",
            extra={
                "failed_item_id": failed_item.id,
                "item_type": item_type,
                "item_id": item_id,
                "error_category": error.category.value,
                "error_message": error.message,
                "retryable": error.retryable,
            }
        )

        return failed_item

    async def get_retryable(self) -> list[FailedItem]:
        """Get all items that can be retried.
        
        Returns:
            List of retryable failed items
        """
        async with self._lock:
            return [item for item in self._queue if item.can_retry]

    async def get_by_category(self, category: ErrorCategory) -> list[FailedItem]:
        """Get failed items by error category.
        
        Args:
            category: Error category to filter by
            
        Returns:
            List of failed items in the category
        """
        async with self._lock:
            return list(self._by_category.get(category, []))

    async def get_for_review(self) -> list[FailedItem]:
        """Get items that need manual review (not retryable or max retries exceeded).
        
        Returns:
            List of items needing manual review
        """
        async with self._lock:
            return [item for item in self._queue if not item.can_retry]

    async def mark_retried(self, item_id: str) -> FailedItem | None:
        """Mark an item as retried, incrementing retry count.
        
        Args:
            item_id: ID of the failed item
            
        Returns:
            Updated FailedItem or None if not found
        """
        async with self._lock:
            for item in self._queue:
                if item.id == item_id:
                    item.retry_count += 1
                    item.last_retry_at = datetime.now(timezone.utc)
                    return item
        return None

    async def remove(self, item_id: str) -> FailedItem | None:
        """Remove an item from the queue (e.g., after successful retry).
        
        Args:
            item_id: ID of the failed item to remove
            
        Returns:
            Removed FailedItem or None if not found
        """
        async with self._lock:
            for i, item in enumerate(self._queue):
                if item.id == item_id:
                    # Remove from main queue
                    del self._queue[i]
                    # Remove from category index
                    cat_list = self._by_category.get(item.error_category, [])
                    if item in cat_list:
                        cat_list.remove(item)
                    return item
        return None

    async def clear(self) -> int:
        """Clear all items from the queue.
        
        Returns:
            Number of items cleared
        """
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            for cat in self._by_category:
                self._by_category[cat].clear()
            return count

    async def get_stats(self) -> dict[str, Any]:
        """Get queue statistics.
        
        Returns:
            Dictionary with queue statistics
        """
        async with self._lock:
            total = len(self._queue)
            retryable = sum(1 for item in self._queue if item.can_retry)
            by_category = {
                cat.value: len(items)
                for cat, items in self._by_category.items()
            }

            return {
                "total": total,
                "retryable": retryable,
                "needs_review": total - retryable,
                "by_category": by_category,
            }

    def __len__(self) -> int:
        """Get queue size."""
        return len(self._queue)

    async def to_list(self) -> list[dict[str, Any]]:
        """Convert all items to list of dictionaries.
        
        Returns:
            List of failed items as dictionaries
        """
        async with self._lock:
            return [item.to_dict() for item in self._queue]


# Global failed items queue instance
_failed_items_queue: FailedItemsQueue | None = None


def get_failed_items_queue() -> FailedItemsQueue:
    """Get the global failed items queue instance.
    
    Returns:
        FailedItemsQueue singleton instance
    """
    global _failed_items_queue
    if _failed_items_queue is None:
        _failed_items_queue = FailedItemsQueue()
    return _failed_items_queue


# Error categorization helper

def categorize_error(error: Exception) -> ErrorCategory:
    """Categorize an exception into an error category.
    
    Args:
        error: Exception to categorize
        
    Returns:
        Appropriate ErrorCategory
        
    Requirement 7.2: Categorize errors as network, parsing, or validation errors.
    """
    if isinstance(error, INECAgentError):
        return error.category

    error_type = type(error).__name__.lower()
    error_msg = str(error).lower()

    # Network-related errors
    network_indicators = [
        "connection", "timeout", "dns", "socket", "network",
        "unreachable", "refused", "reset",
    ]
    if any(ind in error_type or ind in error_msg for ind in network_indicators):
        return ErrorCategory.NETWORK

    # Parsing-related errors
    parsing_indicators = [
        "parse", "json", "xml", "decode", "encode", "format",
        "syntax", "invalid",
    ]
    if any(ind in error_type or ind in error_msg for ind in parsing_indicators):
        return ErrorCategory.PARSING

    # Validation-related errors
    validation_indicators = [
        "validation", "invalid", "constraint", "required",
        "missing", "mismatch",
    ]
    if any(ind in error_type or ind in error_msg for ind in validation_indicators):
        return ErrorCategory.VALIDATION

    # Database-related errors
    db_indicators = [
        "database", "sql", "postgres", "connection pool",
        "integrity", "constraint",
    ]
    if any(ind in error_type or ind in error_msg for ind in db_indicators):
        return ErrorCategory.DATABASE

    return ErrorCategory.UNKNOWN


# Retry decorator with exponential backoff (Requirement 7.3)

def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[Exception], ...] = (NetworkError, DatabaseError),
):
    """Decorator for retry with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        retryable_exceptions: Tuple of exception types to retry
        
    Returns:
        Decorated function with retry logic
        
    Requirement 7.3: Implement retry logic with exponential backoff.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_error = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "delay": delay,
                                "error": str(e),
                                "error_category": categorize_error(e).value,
                            }
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"Max retries exceeded for {func.__name__}",
                            extra={
                                "function": func.__name__,
                                "max_retries": max_retries,
                                "error": str(e),
                            }
                        )

            raise MaxRetriesExceededError(
                f"Max retries ({max_retries}) exceeded for {func.__name__}",
                max_retries=max_retries,
                last_error=last_error,
            )

        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            # For sync functions, run in event loop
            import asyncio
            return asyncio.get_event_loop().run_until_complete(
                async_wrapper(*args, **kwargs)
            )

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator
