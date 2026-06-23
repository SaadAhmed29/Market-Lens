"""
MarketLens - Binance Main Planner
Loads the Binance config and orchestrates the exchange planner.
"""

import logging
import yaml
from pathlib import Path
from datetime import date

from data.binance.exchange_planner import BinanceExchangePlanner

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load and return the Binance config.yml, resolving dynamic values."""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Resolve dynamic end_date
    if config.get("end_date") == "today":
        config["end_date"] = date.today().isoformat()

    return config


def run() -> None:
    """Main entry point: load config and delegate to the exchange planner."""
    logger.info("Loading Binance configuration...")
    config = load_config()

    logger.info("Initializing Binance exchange planner...")
    planner = BinanceExchangePlanner(config)
    
    logger.info("Executing Binance exchange plan...")
    planner.plan()
    
    logger.info("Binance main planner finished successfully.")


if __name__ == "__main__":
    run()
