"""Browser manager with rate limiting for INEC portal scraping.

This module provides a managed Playwright browser instance with:
- Semaphore-based concurrency control
- Exponential backoff retry logic
- Request rate limiting
- Proper resource cleanup via context manager

Requirements: 1.7, 6.5, 7.3
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    Response,
    async_playwright,
)

from app.config import get_settings

logger = logging.getLogger("inec_agent.scraper.browser")


class NetworkError(Exception):
    """Raised when a network-related error occurs during fetching."""

    def __init__(self, url: str, message: str, attempt: int = 0):
        self.url = url
        self.message = message
        self.attempt = attempt
        super().__init__(f"Network error fetching {url}: {message}")


class MaxRetriesExceeded(Exception):
    """Raised when maximum retry attempts have been exhausted."""

    def __init__(self, url: str, max_retries: int, last_error: str | None = None):
        self.url = url
        self.max_retries = max_retries
        self.last_error = last_error
        super().__init__(
            f"Max retries ({max_retries}) exceeded for {url}. Last error: {last_error}"
        )


@dataclass
class FetchResult:
    """Result of a fetch operation."""

    url: str
    status: int
    content: str
    headers: dict
    success: bool
    attempts: int


class BrowserManager:
    """Manages Playwright browser instances with rate limiting.

    This class provides:
    - Semaphore-based concurrency control to limit parallel requests
    - Exponential backoff retry logic for network errors
    - Request delay to avoid overwhelming the target server
    - Context manager pattern for proper resource cleanup

    Requirements:
    - 1.7: Retry with exponential backoff up to 5 attempts
    - 6.5: Rate limiting to avoid overwhelming the INEC portal
    - 7.3: Implement retry logic with exponential backoff

    Example:
        async with BrowserManager() as browser_manager:
            result = await browser_manager.fetch_with_retry("https://example.com")
            print(result.content)
    """

    def __init__(
        self,
        max_concurrent: int = 5,
        request_delay: float = 1.0,
        max_retries: int = 5,
        backoff_factor: float = 2.0,
        timeout: int = 30000,
        headless: bool = True,
    ):
        """Initialize the browser manager.

        Args:
            max_concurrent: Maximum number of concurrent requests (default: 5)
            request_delay: Delay between requests in seconds (default: 1.0)
            max_retries: Maximum retry attempts for failed requests (default: 5)
            backoff_factor: Exponential backoff multiplier (default: 2.0)
            timeout: Page navigation timeout in milliseconds (default: 30000)
            headless: Run browser in headless mode (default: True)
        """
        self.max_concurrent = max_concurrent
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.headless = headless

        # Concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)

        # Track last request time for rate limiting
        self._last_request_time: float = 0.0
        self._request_lock = asyncio.Lock()

        # Playwright resources
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

        logger.info(
            "BrowserManager initialized",
            extra={
                "max_concurrent": max_concurrent,
                "request_delay": request_delay,
                "max_retries": max_retries,
                "backoff_factor": backoff_factor,
            },
        )

    @classmethod
    def from_settings(cls) -> BrowserManager:
        """Create a BrowserManager instance from application settings.

        Returns:
            BrowserManager configured with settings from config.py
        """
        settings = get_settings()
        return cls(
            max_concurrent=settings.scraping.max_concurrent_requests,
            request_delay=settings.scraping.request_delay_seconds,
            max_retries=settings.scraping.max_retries,
            backoff_factor=settings.scraping.backoff_factor,
            timeout=settings.scraping.download_timeout_seconds * 1000,
        )

    async def __aenter__(self) -> BrowserManager:
        """Async context manager entry - initialize browser resources."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - cleanup browser resources."""
        await self.close()

    async def start(self) -> None:
        """Start the Playwright browser and create a context.

        This method initializes:
        - Playwright instance
        - Chromium browser (headless by default)
        - Browser context with appropriate settings
        """
        logger.debug("Starting Playwright browser")

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        logger.info("Browser started successfully")

    async def close(self) -> None:
        """Close browser resources and cleanup.

        This method ensures proper cleanup of:
        - Browser context
        - Browser instance
        - Playwright instance
        """
        logger.debug("Closing browser resources")

        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

        logger.info("Browser resources closed")

    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests.

        Ensures minimum delay between consecutive requests to avoid
        overwhelming the target server (Requirement 6.5).
        """
        async with self._request_lock:
            current_time = asyncio.get_event_loop().time()
            elapsed = current_time - self._last_request_time

            if elapsed < self.request_delay:
                wait_time = self.request_delay - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

            self._last_request_time = asyncio.get_event_loop().time()

    async def _fetch(self, url: str) -> FetchResult:
        """Perform a single fetch operation.

        Args:
            url: The URL to fetch

        Returns:
            FetchResult with response data

        Raises:
            NetworkError: If the fetch fails due to network issues
        """
        if not self._context:
            raise RuntimeError("Browser not started. Call start() or use context manager.")

        page: Page | None = None
        try:
            page = await self._context.new_page()
            page.set_default_timeout(self.timeout)

            logger.debug(f"Fetching URL: {url}")
            response: Response = await page.goto(url, wait_until="networkidle")

            if response is None:
                raise NetworkError(url, "No response received")

            content = await page.content()
            headers = await response.all_headers()

            return FetchResult(
                url=url,
                status=response.status,
                content=content,
                headers=headers,
                success=200 <= response.status < 400,
                attempts=1,
            )

        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Fetch error for {url}: {error_msg}")
            raise NetworkError(url, error_msg)

        finally:
            if page:
                await page.close()

    async def fetch_with_retry(self, url: str) -> FetchResult:
        """Fetch URL with exponential backoff retry.

        Implements retry logic with exponential backoff for network errors
        (Requirements 1.7, 7.3).

        Args:
            url: The URL to fetch

        Returns:
            FetchResult with response data

        Raises:
            MaxRetriesExceeded: If all retry attempts fail
        """
        last_error: str | None = None

        for attempt in range(self.max_retries):
            try:
                async with self.semaphore:
                    await self._enforce_rate_limit()
                    result = await self._fetch(url)
                    result.attempts = attempt + 1

                    if result.success:
                        logger.info(
                            f"Successfully fetched {url}",
                            extra={"attempts": attempt + 1, "status": result.status},
                        )
                        return result

                    # Non-success status code - treat as error for retry
                    last_error = f"HTTP {result.status}"
                    logger.warning(
                        f"Non-success status for {url}: {result.status}",
                        extra={"attempt": attempt + 1},
                    )

            except NetworkError as e:
                last_error = e.message
                logger.warning(
                    f"Network error on attempt {attempt + 1}/{self.max_retries} for {url}: {e.message}"
                )

            # Calculate backoff time for next attempt
            if attempt < self.max_retries - 1:
                wait_time = self.backoff_factor ** attempt
                logger.info(
                    f"Retry {attempt + 1}/{self.max_retries} for {url} after {wait_time:.1f}s"
                )
                await asyncio.sleep(wait_time)

        # All retries exhausted
        logger.error(
            f"Max retries exceeded for {url}",
            extra={"max_retries": self.max_retries, "last_error": last_error},
        )
        raise MaxRetriesExceeded(url, self.max_retries, last_error)

    @asynccontextmanager
    async def get_page(self):
        """Get a managed page instance with rate limiting.

        This context manager provides a page with automatic cleanup
        and rate limiting applied.

        Yields:
            Page: A Playwright page instance

        Example:
            async with browser_manager.get_page() as page:
                await page.goto("https://example.com")
                content = await page.content()
        """
        if not self._context:
            raise RuntimeError("Browser not started. Call start() or use context manager.")

        async with self.semaphore:
            await self._enforce_rate_limit()
            page = await self._context.new_page()
            page.set_default_timeout(self.timeout)
            try:
                yield page
            finally:
                await page.close()

    async def fetch_multiple(self, urls: list[str]) -> list[FetchResult]:
        """Fetch multiple URLs concurrently with rate limiting.

        Args:
            urls: List of URLs to fetch

        Returns:
            List of FetchResult objects (in same order as input URLs)
        """
        tasks = [self.fetch_with_retry(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {url}: {result}")
                processed_results.append(
                    FetchResult(
                        url=url,
                        status=0,
                        content="",
                        headers={},
                        success=False,
                        attempts=self.max_retries,
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    @property
    def is_running(self) -> bool:
        """Check if the browser is currently running."""
        return self._browser is not None and self._context is not None
