"""
MarketLens - Binance Main Planner
Launches the interactive CLI with the exchange pre-set to Binance.
"""

import logging
from pathlib import Path

from data.cli import prompt_config, run_with_config

# Configure logging for the application
log_dir = Path(__file__).resolve().parents[2] / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_dir / "binance.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run() -> None:
    """Main entry point: run interactive CLI with exchange pre-set to binance."""
    logger.info("Starting Binance data pipeline...")
    config = prompt_config(preset_exchange="binance")

    logger.info("Executing Binance download plan...")
    run_with_config(config)

    logger.info("Binance main planner finished successfully.")


if __name__ == "__main__":
    run()
