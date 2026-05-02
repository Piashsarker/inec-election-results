"""Result sheet downloader for INEC election results.

This module handles downloading result sheet images from polling units.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""
from __future__ import annotations


import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

import httpx

from app.config import get_settings
from app.core.scraper.browser import BrowserManager

logger = logging.getLogger("inec_agent.scraper.downloader")


class FileFormat(str, Enum):
    """Supported result sheet file formats."""
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"


@dataclass
class DownloadResult:
    """Result of a download operation."""
    success: bool
    file_path: str | None
    file_format: FileFormat | None
    file_size: int
    error: str | None = None
    attempts: int = 1


class DownloadError(Exception):
    """Raised when a download fails."""

    def __init__(self, url: str, message: str, attempts: int = 0):
        self.url = url
        self.message = message
        self.attempts = attempts
        super().__init__(f"Download error for {url}: {message}")


class ResultSheetDownloader:
    """Downloads result sheet images from polling units.
    
    This class handles:
    - Downloading result sheets in PDF and PNG formats
    - Generating filenames encoding location hierarchy
    - Retry logic for failed downloads
    - Progress tracking
    
    Requirements:
    - 2.1: Download result sheet image for polling unit
    - 2.2: Support PDF and PNG formats
    - 2.3: Store with filename encoding location hierarchy
    - 2.4: Retry up to 3 times on failure
    - 2.5: Log missing results and continue
    """

    def __init__(
        self,
        storage_path: str | None = None,
        max_retries: int = 3,
        browser_manager: BrowserManager | None = None,
    ):
        """Initialize the downloader.
        
        Args:
            storage_path: Directory to store downloaded files
            max_retries: Maximum retry attempts for failed downloads
            browser_manager: Optional BrowserManager for browser-based downloads
        """
        settings = get_settings()
        self.storage_path = Path(storage_path or settings.scraping.storage_path)
        self.max_retries = max_retries
        self.browser = browser_manager

        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Track download progress
        self.total_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0

        logger.info(f"ResultSheetDownloader initialized with storage: {self.storage_path}")

    def _generate_filename(
        self,
        election_type: str,
        state: str,
        lga: str,
        ward: str,
        pu_id: str,
        file_format: FileFormat,
    ) -> str:
        """Generate unique filename encoding location hierarchy.
        
        Args:
            election_type: Election type code
            state: State code
            lga: LGA code
            ward: Ward code
            pu_id: Polling unit ID
            file_format: File format (pdf/png)
            
        Returns:
            Filename string with hierarchy and timestamp
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Sanitize components for filename
        components = [election_type, state, lga, ward, pu_id, timestamp]
        sanitized = [c.replace("/", "_").replace("\\", "_").replace(" ", "_") for c in components]

        filename = "_".join(sanitized) + f".{file_format.value}"
        return filename

    def _detect_format(self, url: str, content_type: str | None = None) -> FileFormat:
        """Detect file format from URL or content type.
        
        Args:
            url: Download URL
            content_type: HTTP Content-Type header
            
        Returns:
            Detected FileFormat
        """
        url_lower = url.lower()

        if url_lower.endswith(".pdf") or (content_type and "pdf" in content_type):
            return FileFormat.PDF
        elif url_lower.endswith(".jpg") or url_lower.endswith(".jpeg"):
            return FileFormat.JPG
        else:
            return FileFormat.PNG

    async def download(
        self,
        url: str,
        election_type: str,
        state: str,
        lga: str,
        ward: str,
        pu_id: str,
    ) -> DownloadResult:
        """Download result sheet image for a polling unit.
        
        Args:
            url: URL of the result sheet image
            election_type: Election type code
            state: State code
            lga: LGA code
            ward: Ward code
            pu_id: Polling unit ID
            
        Returns:
            DownloadResult with file path and status
        """
        self.total_downloads += 1
        last_error: str | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Download attempt {attempt}/{self.max_retries} for {url}")

                # Use httpx for direct downloads
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, follow_redirects=True)

                    if response.status_code == 404:
                        # Result sheet not available
                        logger.warning(
                            f"Result sheet not available for PU {pu_id}",
                            extra={"url": url, "state": state, "lga": lga, "ward": ward},
                        )
                        self.failed_downloads += 1
                        return DownloadResult(
                            success=False,
                            file_path=None,
                            file_format=None,
                            file_size=0,
                            error="Result sheet not available",
                            attempts=attempt,
                        )

                    response.raise_for_status()

                    # Detect format and generate filename
                    content_type = response.headers.get("content-type", "")
                    file_format = self._detect_format(url, content_type)
                    filename = self._generate_filename(
                        election_type, state, lga, ward, pu_id, file_format
                    )

                    # Save file
                    file_path = self.storage_path / filename
                    file_path.write_bytes(response.content)

                    file_size = len(response.content)
                    self.successful_downloads += 1

                    logger.info(
                        f"Downloaded result sheet: {filename}",
                        extra={"size": file_size, "format": file_format.value},
                    )

                    return DownloadResult(
                        success=True,
                        file_path=str(file_path),
                        file_format=file_format,
                        file_size=file_size,
                        attempts=attempt,
                    )

            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}"
                logger.warning(f"HTTP error on attempt {attempt}: {last_error}")

            except httpx.RequestError as e:
                last_error = str(e)
                logger.warning(f"Request error on attempt {attempt}: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Unexpected error on attempt {attempt}: {last_error}")

            # Wait before retry (simple backoff)
            if attempt < self.max_retries:
                import asyncio
                await asyncio.sleep(attempt * 2)

        # All retries exhausted
        self.failed_downloads += 1
        logger.error(
            f"Failed to download result sheet after {self.max_retries} attempts",
            extra={
                "url": url,
                "election_type": election_type,
                "state": state,
                "lga": lga,
                "ward": ward,
                "pu_id": pu_id,
                "last_error": last_error,
            },
        )

        return DownloadResult(
            success=False,
            file_path=None,
            file_format=None,
            file_size=0,
            error=last_error,
            attempts=self.max_retries,
        )

    def get_progress(self) -> dict:
        """Get download progress statistics.
        
        Returns:
            Dictionary with total, completed, and failed counts
        """
        return {
            "total": self.total_downloads,
            "completed": self.successful_downloads,
            "failed": self.failed_downloads,
        }

    def reset_progress(self) -> None:
        """Reset progress counters."""
        self.total_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
