"""
MarketLens - Data Pipeline CLI
Interactive prompts for selecting data download configuration.
Reads available options from meta_data.data_config and lets the
user pick values via questionary.
"""

import logging
from data.data_downloader import DataFetcher
from utils.db import run_cli

logger = logging.getLogger(__name__)


def prompt_config(preset_exchange: str | None = None) -> dict:
    """Run interactive CLI prompts and return a fully-resolved config dict.

    Parameters
    ----------
    preset_exchange : str or None
        If provided, skip the exchange prompt and use this value directly
        (used by exchange-specific entry points like binance/main.py).
    """
    options = [
        'exchange',
        'symbols',
        'time_horizon',
        'fill_missing_data',
        'retries',
        'retry_delay',
        'start_date',
        'end_date'
    ]
    return run_cli(options, preset_exchange=preset_exchange)


def run_with_config(config: dict) -> None:
    """Create a DataFetcher from *config* and download all selected symbols."""
    downloader = DataFetcher(config)
    downloader.download_all(config["symbols"])

