"""
MarketLens - Config Utils
Provides utility functions for loading configurations.
"""

import yaml
from pathlib import Path
from datetime import timezone, datetime

def load_config(config_path: str | Path) -> dict:
    """Load and return a generic YAML config file as a dict."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_exchange_config(config_path: Path) -> dict:
    """Load and return an exchange config.yml, resolving dynamic values."""
    config = load_config(config_path)

    # Resolve dynamic end_date
    if config.get("end_date") == "now":
        config["end_date"] = datetime.now(timezone.utc).isoformat()

    return config
