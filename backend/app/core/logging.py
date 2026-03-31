"""Logging configuration for INEC Election Results Agent.

This module provides structured JSON logging with rotating file handlers,
configurable log levels, and consistent formatting across the application.

Requirements: 7.1, 7.2, 7.6
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging.
    
    Produces log entries with consistent structure including:
    - timestamp (ISO 8601 format)
    - level (log level name)
    - logger (logger name)
    - message (log message)
    - Additional context fields from extra dict
    
    Requirements: 7.1 (log all operations with timestamps, operation type, status)
    """
    
    def __init__(
        self,
        *,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        include_location: bool = False,
    ):
        """Initialize JSON formatter.
        
        Args:
            include_timestamp: Include ISO timestamp in output
            include_level: Include log level in output
            include_logger: Include logger name in output
            include_location: Include file/line location info
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_location = include_location
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data: dict[str, Any] = {}
        
        # Core fields (Requirement 7.1: timestamp, operation type, status)
        if self.include_timestamp:
            log_data["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        if self.include_level:
            log_data["level"] = record.levelname
        
        if self.include_logger:
            log_data["logger"] = record.name
        
        # Message
        log_data["message"] = record.getMessage()
        
        # Location info (optional, useful for debugging)
        if self.include_location:
            log_data["location"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }
        
        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Include extra fields from record
        # These are added via logger.info("msg", extra={...})
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in {
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "taskName",
            }
        }
        if extra_fields:
            log_data["context"] = extra_fields
        
        return json.dumps(log_data, default=str)


class TextFormatter(logging.Formatter):
    """Standard text formatter for console output.
    
    Produces human-readable log entries for development/debugging.
    """
    
    DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
    ):
        """Initialize text formatter.
        
        Args:
            fmt: Log format string
            datefmt: Date format string
        """
        super().__init__(
            fmt=fmt or self.DEFAULT_FORMAT,
            datefmt=datefmt or self.DEFAULT_DATE_FORMAT,
        )


def _ensure_log_directory(log_path: str) -> None:
    """Ensure the log directory exists.
    
    Args:
        log_path: Path to log file
    """
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)


def _create_console_handler(
    level: int,
    use_json: bool = False,
) -> logging.StreamHandler:
    """Create console handler with appropriate formatter.
    
    Args:
        level: Logging level
        use_json: Use JSON format for console output
        
    Returns:
        Configured console handler
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())
    
    return handler


def _create_file_handler(
    log_path: str,
    level: int,
    max_bytes: int,
    backup_count: int,
) -> logging.handlers.RotatingFileHandler:
    """Create rotating file handler with JSON formatter.
    
    Args:
        log_path: Path to log file
        level: Logging level
        max_bytes: Maximum file size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured rotating file handler
        
    Requirements: 7.6 (configurable log levels)
    """
    _ensure_log_directory(log_path)
    
    handler = logging.handlers.RotatingFileHandler(
        filename=log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(JSONFormatter(include_location=True))
    
    return handler


# Default logging configuration dict (for reference/compatibility)
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "json": {
            "()": JSONFormatter,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/agent.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": "DEBUG",
        }
    },
    "loggers": {
        "inec_agent": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        }
    }
}


def configure_logging(
    *,
    level: Optional[str] = None,
    log_format: Optional[str] = None,
    file_path: Optional[str] = None,
    max_file_size_mb: Optional[int] = None,
    backup_count: Optional[int] = None,
    console_json: bool = False,
) -> None:
    """Configure application logging using settings from config.
    
    Sets up both console and file handlers with appropriate formatters.
    Console uses text format by default for readability, file uses JSON
    for structured logging and analysis.
    
    Args:
        level: Override log level (DEBUG, INFO, WARNING, ERROR)
        log_format: Override log format (json or text)
        file_path: Override log file path
        max_file_size_mb: Override max file size in MB
        backup_count: Override backup file count
        console_json: Use JSON format for console output
        
    Requirements: 7.1, 7.6
    """
    # Import here to avoid circular imports
    from app.config import get_settings
    
    settings = get_settings()
    log_settings = settings.logging
    
    # Resolve configuration values
    log_level_str = level or log_settings.level.value
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    log_file = file_path or log_settings.file_path
    max_bytes = (max_file_size_mb or log_settings.max_file_size_mb) * 1024 * 1024
    backups = backup_count or log_settings.backup_count
    
    # Get root logger for the application
    root_logger = logging.getLogger("inec_agent")
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = _create_console_handler(
        level=log_level,
        use_json=console_json or (log_format == "json"),
    )
    root_logger.addHandler(console_handler)
    
    # Add file handler if path is configured
    if log_file:
        file_handler = _create_file_handler(
            log_path=log_file,
            level=logging.DEBUG,  # File always captures DEBUG for analysis
            max_bytes=max_bytes,
            backup_count=backups,
        )
        root_logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    root_logger.propagate = False
    
    # Log configuration complete
    root_logger.info(
        "Logging configured",
        extra={
            "log_level": log_level_str,
            "log_file": log_file,
            "max_file_size_mb": max_file_size_mb or log_settings.max_file_size_mb,
            "backup_count": backups,
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified module.
    
    Creates a child logger under the 'inec_agent' namespace to ensure
    consistent configuration and formatting.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started", extra={"job_id": "123"})
    """
    # Create child logger under inec_agent namespace
    if name.startswith("inec_agent."):
        return logging.getLogger(name)
    return logging.getLogger(f"inec_agent.{name}")
