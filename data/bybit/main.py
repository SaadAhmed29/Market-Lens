"""
MarketLens - Bybit Main Planner
Launches the interactive CLI with the exchange pre-set to Bybit.
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
        logging.FileHandler(log_dir / "bybit.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run() -> None:
    """Main entry point: run interactive CLI with exchange pre-set to bybit."""
    logger.info("Starting Bybit data pipeline...")
    config = prompt_config(preset_exchange="bybit")

    logger.info("Executing Bybit download plan...")
    run_with_config(config)

    logger.info("Bybit main planner finished successfully.")


if __name__ == "__main__":
    run()
