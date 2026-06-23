"""
MarketLens - Bybit Main Planner
Loads the Bybit config and orchestrates the exchange planner.
"""

import yaml
from pathlib import Path
from datetime import date

from data.bybit.exchange_planner import BybitExchangePlanner


def load_config() -> dict:
    """Load and return the Bybit config.yml, resolving dynamic values."""
    config_path = Path(__file__).parent / "config.yml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Resolve dynamic end_date
    if config.get("end_date") == "today":
        config["end_date"] = date.today().isoformat()

    return config


def run() -> None:
    """Main entry point: load config and delegate to the exchange planner."""
    config = load_config()

    # TODO: Add logging initialization
    # TODO: Add config validation via utils.schema

    planner = BybitExchangePlanner(config)
    planner.plan()


if __name__ == "__main__":
    run()
