"""Result sheet downloader for INEC election results.

Downloads result sheet images from polling units and uploads them to
cloud storage (Cloudflare R2 / S3).  Falls back to local filesystem
when cloud credentials are not configured.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

import httpx

from app.config import get_settings
from app.core.scraper.browser import BrowserManager
from app.core.storage.service import StorageService

logger = logging.getLogger("inec_agent.scraper.downloader")


class FileFormat(StrEnum):
    """Supported result sheet file formats."""
    PDF = "pdf"
    PNG = "png"
    JPG = "jpg"


@dataclass
class DownloadResult:
    """Result of a download operation."""
    success: bool
    file_path: str | None          # Local file path (always set on success)
    storage_url: str | None        # Cloud URL (R2/S3) or local path
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
        storage_service: StorageService | None = None,
    ):
        """Initialize the downloader.

        Args:
            storage_path: Local directory for temporary/fallback file storage
            max_retries: Maximum retry attempts for failed downloads
            browser_manager: Optional BrowserManager for browser-based downloads
            storage_service: Cloud storage service (created from settings if None)
        """
        settings = get_settings()
        self.storage_path = Path(storage_path or settings.scraping.storage_path)
        self.max_retries = max_retries
        self.browser = browser_manager

        # Initialise cloud storage (auto-detects credentials from settings)
        if storage_service is not None:
            self.storage = storage_service
        else:
            self.storage = StorageService.from_settings(settings)

        # Ensure local directory exists (used as temp/fallback)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory deduplication — tracks (pu_id, url) pairs already
        # processed in this downloader instance (within a single job run).
        self._seen_pu_ids: set[str] = set()
        self._seen_urls: set[str] = set()

        # Track download progress
        self.total_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.skipped_duplicates = 0

        logger.info(
            f"ResultSheetDownloader initialised | local={self.storage_path} | "
            f"cloud={'enabled' if self.storage.is_cloud_enabled() else 'disabled (local fallback)'}"
        )

    def _build_object_key(
        self,
        election_type: str,
        state: str,
        lga: str,
        ward: str,
        pu_id: str,
        filename: str,
    ) -> str:
        """Build the S3 / R2 object key (path inside bucket).

        Structure: result_sheets/{election}/{state}/{lga}/{ward}/{filename}
        """

        def _clean(s: str) -> str:
            return s.replace(" ", "_").replace("/", "_").lower()

        return "/".join([
            "result_sheets",
            _clean(election_type),
            _clean(state),
            _clean(lga),
            _clean(ward),
            filename,
        ])

    def _deterministic_object_key(
        self,
        election_type: str,
        state: str,
        lga: str,
        ward: str,
        pu_id: str,
        ext: str = "jpg",
    ) -> str:
        """Build a stable, timestamp-free object key for a polling unit.

        This key is used for duplicate detection — the same polling unit
        always maps to the same key, so HeadObject on R2 tells us whether
        the image was already uploaded in a previous job run.

        Structure: result_sheets/{election}/{state}/{lga}/{ward}/{pu_id}.{ext}
        """
        def _clean(s: str) -> str:
            return s.replace(" ", "_").replace("/", "_").lower()

        return "/".join([
            "result_sheets",
            _clean(election_type),
            _clean(state),
            _clean(lga),
            _clean(ward),
            f"{_clean(pu_id)}.{ext}",
        ])

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

        Deduplication is applied at three layers:
          1. In-memory URL check — skips if the same URL was already
             fetched in this job run (fastest).
          2. In-memory PU ID check — skips if the same polling unit was
             already processed in this job run.
          3. Cloud storage check (HeadObject) — skips if the image was
             already uploaded in a *previous* job run (cross-run dedup).

        Args:
            url: URL of the result sheet image
            election_type: Election type code
            state: State code
            lga: LGA code
            ward: Ward code
            pu_id: Polling unit ID

        Returns:
            DownloadResult with file path and status.
            When skipped, ``success=True`` and ``error="duplicate"`` is set.
        """
        self.total_downloads += 1

        # ── Layer 1: in-memory URL dedup (same run) ──────────────────────
        if url in self._seen_urls:
            logger.info(f"Skipping duplicate URL (same run): {url}")
            self.skipped_duplicates += 1
            return DownloadResult(
                success=True,
                file_path=None,
                storage_url=None,
                file_format=None,
                file_size=0,
                error="duplicate:url",
                attempts=0,
            )

        # ── Layer 2: in-memory PU ID dedup (same run) ────────────────────
        if pu_id in self._seen_pu_ids:
            logger.info(f"Skipping duplicate PU ID (same run): {pu_id}")
            self.skipped_duplicates += 1
            return DownloadResult(
                success=True,
                file_path=None,
                storage_url=None,
                file_format=None,
                file_size=0,
                error="duplicate:pu_id",
                attempts=0,
            )

        # ── Layer 3: cloud storage dedup (cross-run) ─────────────────────
        # Detect likely extension from the URL before making the HeadObject call
        ext = "pdf" if url.lower().endswith(".pdf") else "jpg"
        dedup_key = self._deterministic_object_key(
            election_type, state, lga, ward, pu_id, ext
        )

        if await self.storage.object_exists(dedup_key):
            logger.info(
                f"Skipping duplicate — already in storage: {dedup_key}"
            )
            self.skipped_duplicates += 1
            # Mark as seen so subsequent requests in this run are caught cheaper
            self._seen_pu_ids.add(pu_id)
            self._seen_urls.add(url)
            existing_url = self.storage._build_url(dedup_key)
            return DownloadResult(
                success=True,
                file_path=None,
                storage_url=existing_url,
                file_format=FileFormat.JPG if ext == "jpg" else FileFormat.PDF,
                file_size=0,
                error="duplicate:storage",
                attempts=0,
            )

        # ── Not a duplicate — proceed with download ───────────────────────
        self._seen_urls.add(url)
        self._seen_pu_ids.add(pu_id)

        last_error: str | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Download attempt {attempt}/{self.max_retries} for {url}")

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, follow_redirects=True)

                    if response.status_code == 404:
                        logger.warning(
                            f"Result sheet not available for PU {pu_id}",
                            extra={"url": url, "state": state, "lga": lga, "ward": ward},
                        )
                        self.failed_downloads += 1
                        return DownloadResult(
                            success=False,
                            file_path=None,
                            storage_url=None,
                            file_format=None,
                            file_size=0,
                            error="Result sheet not available",
                            attempts=attempt,
                        )

                    response.raise_for_status()

                    # Detect format and generate stable filename
                    content_type = response.headers.get("content-type", "")
                    file_format = self._detect_format(url, content_type)

                    # Use deterministic key (no timestamp) for storage so the
                    # same polling unit always maps to the same R2 object.
                    object_key = self._deterministic_object_key(
                        election_type, state, lga, ward, pu_id,
                        file_format.value,
                    )

                    # Also save locally under a readable name
                    filename = self._generate_filename(
                        election_type, state, lga, ward, pu_id, file_format
                    )
                    file_path = self.storage_path / filename
                    file_path.write_bytes(response.content)
                    file_size = len(response.content)

                    # Upload to R2 / S3
                    storage_url = await self.storage.upload_bytes(
                        response.content,
                        object_key,
                        content_type=content_type or "image/jpeg",
                        skip_if_exists=False,  # we already checked above
                    )

                    self.successful_downloads += 1
                    logger.info(
                        f"Downloaded & stored: {object_key} "
                        f"({file_size:,} bytes) → {storage_url}"
                    )

                    return DownloadResult(
                        success=True,
                        file_path=str(file_path),
                        storage_url=storage_url,
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

            if attempt < self.max_retries:
                import asyncio
                await asyncio.sleep(attempt * 2)

        self.failed_downloads += 1
        logger.error(
            f"Failed to download result sheet after {self.max_retries} attempts",
            extra={
                "url": url, "election_type": election_type,
                "state": state, "lga": lga, "ward": ward,
                "pu_id": pu_id, "last_error": last_error,
            },
        )

        return DownloadResult(
            success=False,
            file_path=None,
            storage_url=None,
            file_format=None,
            file_size=0,
            error=last_error,
            attempts=self.max_retries,
        )

    def get_progress(self) -> dict:
        """Get download progress statistics.

        Returns:
            Dictionary with total, completed, skipped, and failed counts
        """
        return {
            "total": self.total_downloads,
            "completed": self.successful_downloads,
            "skipped_duplicates": self.skipped_duplicates,
            "failed": self.failed_downloads,
        }

    def reset_progress(self) -> None:
        """Reset progress counters and deduplication state."""
        self.total_downloads = 0
        self.successful_downloads = 0
        self.failed_downloads = 0
        self.skipped_duplicates = 0
        self._seen_urls.clear()
        self._seen_pu_ids.clear()
