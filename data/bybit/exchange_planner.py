"""
MarketLens - Bybit Exchange Planner
Handles planning and coordination of data downloads for Bybit.
"""

import logging
from data.data_downloader import DataDownloader

logger = logging.getLogger(__name__)


class BybitExchangePlanner:
    """Plans and coordinates data fetching tasks for the Bybit exchange."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self.exchange = config["exchange"]
        self.symbols = config["symbols"]
        self.time_horizon = config["time_horizon"]
        self.start_date = config["start_date"]
        self.end_date = config["end_date"]
        self.retries = config["retries"]
        self.retry_delay = config["retry_delay"]

        self.downloader = DataDownloader(config)

    def plan(self) -> None:
        """Build and execute the download plan for all configured symbols."""
        logger.info(f"Starting Bybit download plan for {len(self.symbols)} symbols.")
        
        for symbol in self.symbols:
            try:
                self.downloader.download(symbol)
                logger.info(f"Successfully finished processing {symbol} on Bybit.")
            except Exception as exc:
                logger.error(f"Failed to process {symbol} on Bybit: {exc}")
                
        logger.info("Bybit download plan completed.")
