"""
MarketLens - Data Downloader
Generic data downloader shared across all exchanges.
Handles HTTP requests, retries, and raw data retrieval.
"""


class DataDownloader:
    """Downloads market data from exchange APIs with retry logic."""

    def __init__(self, exchange: str, base_url: str, retries: int = 3, retry_delay: int = 5) -> None:
        self.exchange = exchange
        self.base_url = base_url
        self.retries = retries
        self.retry_delay = retry_delay

        # TODO: Initialize HTTP session / async client

    def download(self, symbol: str, start_date: str, end_date: str, time_horizon: str) -> None:
        """Download OHLCV data for a single symbol over the given date range."""
        # TODO: Build API request URL from parameters
        # TODO: Execute request with retry logic
        # TODO: Parse and return raw data
        pass

    def _retry_request(self, url: str) -> None:
        """Execute a request with configurable retry logic."""
        # TODO: Implement exponential backoff or fixed-delay retries
        pass
