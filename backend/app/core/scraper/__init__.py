"""Web scraping components for INEC portal."""

from app.core.scraper.browser import (
    BrowserManager,
    FetchResult,
    MaxRetriesExceeded,
    NetworkError,
)
from app.core.scraper.navigator import (
    PortalNavigator,
    NavigationError,
    ElectionType,
    State,
    LGA,
    Ward,
    PollingUnit,
)
from app.core.scraper.downloader import (
    ResultSheetDownloader,
    DownloadResult,
    DownloadError,
    FileFormat,
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
