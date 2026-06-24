"""
MarketLens - Config Utils
Provides utility functions for loading configurations.
"""

import yaml
from pathlib import Path
from datetime import date

def load_exchange_config(config_path: Path) -> dict:
    """Load and return an exchange config.yml, resolving dynamic values."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Resolve dynamic end_date
    if config.get("end_date") == "today":
        config["end_date"] = date.today().isoformat()

    return config
