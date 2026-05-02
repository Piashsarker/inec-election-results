"""Web scraping components for INEC portal."""

from app.core.scraper.browser import (
    BrowserManager,
    FetchResult,
    MaxRetriesExceeded,
    NetworkError,
)
from app.core.scraper.downloader import (
    DownloadError,
    DownloadResult,
    FileFormat,
    ResultSheetDownloader,
)
from app.core.scraper.navigator import (
    LGA,
    ElectionType,
    NavigationError,
    PollingUnit,
    PortalNavigator,
    State,
    Ward,
)

__all__ = [
    "BrowserManager",
    "FetchResult",
    "NetworkError",
    "MaxRetriesExceeded",
    "PortalNavigator",
    "NavigationError",
    "ElectionType",
    "State",
    "LGA",
    "Ward",
    "PollingUnit",
    "ResultSheetDownloader",
    "DownloadResult",
    "DownloadError",
    "FileFormat",
]
