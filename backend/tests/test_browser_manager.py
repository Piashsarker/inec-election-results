"""Tests for BrowserManager with rate limiting and retry logic.

Requirements tested: 1.7, 6.5, 7.3
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.scraper.browser import (
    BrowserManager,
    FetchResult,
    MaxRetriesExceeded,
    NetworkError,
)


class TestBrowserManagerInit:
    """Test BrowserManager initialization."""

    def test_default_initialization(self):
        """Test default parameter values."""
        manager = BrowserManager()
        assert manager.max_concurrent == 5
        assert manager.request_delay == 1.0
        assert manager.max_retries == 5
        assert manager.backoff_factor == 2.0
        assert manager.timeout == 30000
        assert manager.headless is True

    def test_custom_initialization(self):
        """Test custom parameter values."""
        manager = BrowserManager(
            max_concurrent=10,
            request_delay=2.0,
            max_retries=3,
            backoff_factor=1.5,
            timeout=60000,
            headless=False,
        )
        assert manager.max_concurrent == 10
        assert manager.request_delay == 2.0
        assert manager.max_retries == 3
        assert manager.backoff_factor == 1.5
        assert manager.timeout == 60000
        assert manager.headless is False

    def test_semaphore_created_with_max_concurrent(self):
        """Test semaphore is created with correct limit."""
        manager = BrowserManager(max_concurrent=3)
        assert manager.semaphore._value == 3


class TestNetworkError:
    """Test NetworkError exception."""

    def test_network_error_attributes(self):
        """Test NetworkError stores correct attributes."""
        error = NetworkError("https://example.com", "Connection timeout", attempt=2)
        assert error.url == "https://example.com"
        assert error.message == "Connection timeout"
        assert error.attempt == 2

    def test_network_error_message(self):
        """Test NetworkError string representation."""
        error = NetworkError("https://example.com", "Connection timeout")
        assert "https://example.com" in str(error)
        assert "Connection timeout" in str(error)


class TestMaxRetriesExceeded:
    """Test MaxRetriesExceeded exception."""

    def test_max_retries_exceeded_attributes(self):
        """Test MaxRetriesExceeded stores correct attributes."""
        error = MaxRetriesExceeded("https://example.com", 5, "Timeout")
        assert error.url == "https://example.com"
        assert error.max_retries == 5
        assert error.last_error == "Timeout"

    def test_max_retries_exceeded_message(self):
        """Test MaxRetriesExceeded string representation."""
        error = MaxRetriesExceeded("https://example.com", 5, "Timeout")
        assert "5" in str(error)
        assert "https://example.com" in str(error)
        assert "Timeout" in str(error)


class TestFetchResult:
    """Test FetchResult dataclass."""

    def test_fetch_result_creation(self):
        """Test FetchResult stores correct values."""
        result = FetchResult(
            url="https://example.com",
            status=200,
            content="<html></html>",
            headers={"content-type": "text/html"},
            success=True,
            attempts=1,
        )
        assert result.url == "https://example.com"
        assert result.status == 200
        assert result.content == "<html></html>"
        assert result.headers == {"content-type": "text/html"}
        assert result.success is True
        assert result.attempts == 1


class TestBrowserManagerRateLimiting:
    """Test rate limiting functionality (Requirement 6.5)."""

    @pytest.mark.asyncio
    async def test_rate_limiting_enforces_delay(self):
        """Test that rate limiting enforces minimum delay between requests."""
        manager = BrowserManager(request_delay=0.1)

        # Record times when rate limit is enforced
        times = []

        async def record_time():
            await manager._enforce_rate_limit()
            times.append(asyncio.get_event_loop().time())

        # Make multiple calls
        await record_time()
        await record_time()
        await record_time()

        # Check delays between calls
        for i in range(1, len(times)):
            delay = times[i] - times[i - 1]
            # Allow small tolerance for timing
            assert delay >= 0.09, f"Delay {delay} is less than expected 0.1s"


class TestBrowserManagerRetry:
    """Test retry logic with exponential backoff (Requirements 1.7, 7.3)."""

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self):
        """Test that network errors trigger retries."""
        manager = BrowserManager(max_retries=3, backoff_factor=1.0, request_delay=0.01)

        call_count = 0

        async def mock_fetch(url):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError(url, "Connection failed")
            return FetchResult(
                url=url,
                status=200,
                content="Success",
                headers={},
                success=True,
                attempts=call_count,
            )

        # Mock the internal _fetch method
        manager._fetch = mock_fetch
        manager._context = MagicMock()  # Pretend browser is started

        result = await manager.fetch_with_retry("https://example.com")

        assert call_count == 3
        assert result.success is True
        assert result.content == "Success"

    @pytest.mark.asyncio
    async def test_max_retries_exceeded_raises_exception(self):
        """Test that exceeding max retries raises MaxRetriesExceeded."""
        manager = BrowserManager(max_retries=3, backoff_factor=1.0, request_delay=0.01)

        async def mock_fetch(url):
            raise NetworkError(url, "Connection failed")

        manager._fetch = mock_fetch
        manager._context = MagicMock()

        with pytest.raises(MaxRetriesExceeded) as exc_info:
            await manager.fetch_with_retry("https://example.com")

        assert exc_info.value.max_retries == 3
        assert exc_info.value.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that backoff increases exponentially."""
        manager = BrowserManager(max_retries=4, backoff_factor=2.0, request_delay=0.01)

        sleep_times = []
        original_sleep = asyncio.sleep

        async def mock_sleep(duration):
            sleep_times.append(duration)
            await original_sleep(0.001)  # Minimal actual sleep

        call_count = 0

        async def mock_fetch(url):
            nonlocal call_count
            call_count += 1
            raise NetworkError(url, "Connection failed")

        manager._fetch = mock_fetch
        manager._context = MagicMock()

        with patch("asyncio.sleep", mock_sleep):
            with pytest.raises(MaxRetriesExceeded):
                await manager.fetch_with_retry("https://example.com")

        # Check exponential backoff: 2^0=1, 2^1=2, 2^2=4
        # Filter out rate limiting sleeps (which are small)
        backoff_sleeps = [t for t in sleep_times if t >= 0.5]
        assert len(backoff_sleeps) == 3  # 3 retries after first attempt
        assert backoff_sleeps[0] == 1.0  # 2^0
        assert backoff_sleeps[1] == 2.0  # 2^1
        assert backoff_sleeps[2] == 4.0  # 2^2


class TestBrowserManagerConcurrency:
    """Test semaphore-based concurrency control."""

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrent_requests(self):
        """Test that semaphore limits concurrent requests."""
        manager = BrowserManager(max_concurrent=2, request_delay=0.01)

        concurrent_count = 0
        max_concurrent_observed = 0

        async def mock_fetch(url):
            nonlocal concurrent_count, max_concurrent_observed
            concurrent_count += 1
            max_concurrent_observed = max(max_concurrent_observed, concurrent_count)
            await asyncio.sleep(0.05)  # Simulate work
            concurrent_count -= 1
            return FetchResult(
                url=url,
                status=200,
                content="OK",
                headers={},
                success=True,
                attempts=1,
            )

        manager._fetch = mock_fetch
        manager._context = MagicMock()

        # Start 5 concurrent requests
        urls = [f"https://example.com/{i}" for i in range(5)]
        await manager.fetch_multiple(urls)

        # Should never exceed max_concurrent
        assert max_concurrent_observed <= 2


class TestBrowserManagerContextManager:
    """Test context manager functionality."""

    def test_is_running_false_initially(self):
        """Test is_running is False before start."""
        manager = BrowserManager()
        assert manager.is_running is False

    @pytest.mark.asyncio
    async def test_fetch_without_start_raises_error(self):
        """Test that fetching without starting raises RuntimeError."""
        manager = BrowserManager()

        with pytest.raises(RuntimeError, match="Browser not started"):
            await manager._fetch("https://example.com")

    @pytest.mark.asyncio
    async def test_get_page_without_start_raises_error(self):
        """Test that get_page without starting raises RuntimeError."""
        manager = BrowserManager()

        with pytest.raises(RuntimeError, match="Browser not started"):
            async with manager.get_page():
                pass
