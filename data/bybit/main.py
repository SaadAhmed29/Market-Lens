"""
MarketLens - Bybit Main Planner
Runs automated via task scheduler, downloading data based on DB config.
"""

import logging
from pathlib import Path
from datetime import datetime, timezone
import yaml

from data.data_downloader import DataFetcher
from utils.db import load_data_config, update_data_config_dates

# Configure logging for the application
log_dir = Path(__file__).resolve().parents[2] / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_dir / "bybit.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run() -> None:
    """Main entry point: run automated data pipeline for Bybit."""
    logger.info("Starting Bybit data pipeline...")
    
    # Load configs from DB
    configs = load_data_config("bybit")
    
    # Load local config for processing settings
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, "r") as f:
        local_config = yaml.safe_load(f)
        
    fill_missing_data = local_config.get("fill_missing_data", "interpolation")
    retries = local_config.get("retries", 3)
    retry_delay = local_config.get("retry_delay", 5)

    for row in configs:
        symbol = row["symbol"]
        time_horizon = row["time_horizon"]
        start_date = row["start_date"]
        
        now_dt = datetime.now(timezone.utc)
        
        fetcher_config = {
            "exchange": "bybit",
            "time_horizon": time_horizon,
            "start_date": start_date.strftime("%Y-%m-%d %H:%M:%S") if isinstance(start_date, datetime) else str(start_date),
            "end_date": now_dt.strftime("%Y-%m-%d %H:%M:%S"),
            "fill_missing_data": fill_missing_data,
            "retries": retries,
            "retry_delay": retry_delay
        }
        
        logger.info(f"Executing Bybit download plan for {symbol} ({time_horizon})...")
        fetcher = DataFetcher(fetcher_config)
        
        try:
            fetcher.download(symbol)
            update_data_config_dates("bybit", symbol, time_horizon, start_date, now_dt)
            logger.info(f"Successfully finished processing {symbol} on Bybit.")
        except Exception as exc:
            logger.error(f"Failed to process {symbol} on Bybit: {exc}")

    logger.info("Bybit main planner finished successfully.")


if __name__ == "__main__":
    run()
