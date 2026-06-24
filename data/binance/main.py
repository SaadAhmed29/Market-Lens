"""
MarketLens - Binance Main Planner
Loads the Binance config and orchestrates the exchange planner.
"""

import logging
from pathlib import Path

from data.data_downloader import DataFetcher
from utils.config import load_exchange_config

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def run() -> None:
    """Main entry point: load config and delegate to the data downloader."""
    logger.info("Loading Binance configuration...")
    config_path = Path(__file__).parent / "config.yml"
    config = load_exchange_config(config_path)

    logger.info("Initializing Binance data downloader...")
    downloader = DataFetcher(config)
    
    logger.info("Executing Binance download plan...")
    downloader.download_all(config["symbols"])
    
    logger.info("Binance main planner finished successfully.")


if __name__ == "__main__":
    run()
