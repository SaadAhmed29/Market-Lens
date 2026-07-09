"""
MarketLens - Data Pipeline CLI
Interactive prompts for selecting data download configuration.
Reads available options from meta_data.data_config and lets the
user pick values via questionary.
"""

import logging
from datetime import datetime, timezone

import questionary
from questionary import Style

from utils.db import create_meta_data_schema, load_db_config
from data.data_downloader import DataFetcher

logger = logging.getLogger(__name__)

# Styling for the CLI prompts
_style = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "fg:white bold"),
    ("answer", "fg:green bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("selected", "fg:green"),
])


def prompt_config(preset_exchange: str | None = None) -> dict:
    """Run interactive CLI prompts and return a fully-resolved config dict.

    Parameters
    ----------
    preset_exchange : str or None
        If provided, skip the exchange prompt and use this value directly
        (used by exchange-specific entry points like binance/main.py).
    """
    # Ensure DB config table exists with defaults
    create_meta_data_schema()
    db_config = load_db_config()

    # --- exchange ---
    if preset_exchange:
        exchange = preset_exchange
        print(f"Exchange: {exchange}")
    else:
        exchange = questionary.select(
            "Select exchange:",
            choices=db_config["exchange"],
            style=_style,
        ).ask()
        if exchange is None:
            raise KeyboardInterrupt("Prompt cancelled.")

    # --- symbols ---
    symbols = questionary.checkbox(
        "Select symbols:",
        choices=db_config["symbols"],
        style=_style,
        validate=lambda sel: len(sel) > 0 or "Select at least one symbol.",
    ).ask()
    if symbols is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    # --- time_horizon (single select) ---
    time_horizon = questionary.select(
        "Select time horizon:",
        choices=db_config["time_horizons"],
        style=_style,
    ).ask()
    if time_horizon is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    # --- fill_missing_data ---
    fill_missing_data = questionary.select(
        "Select fill strategy for missing data:",
        choices=db_config["fill_missing_data"],
        style=_style,
    ).ask()
    if fill_missing_data is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    # --- retries ---
    retries = questionary.select(
        "Select number of retries:",
        choices=[str(r) for r in db_config["retries"]],
        style=_style,
    ).ask()
    if retries is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    # --- retry_delay ---
    retry_delay = questionary.select(
        "Select retry delay (seconds):",
        choices=[str(r) for r in db_config["retry_delay"]],
        style=_style,
    ).ask()
    if retry_delay is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    # --- start_date ---
    start_date = questionary.text(
        "Enter start date (YYYY-MM-DD):",
        validate=lambda val: _validate_date(val) or "Invalid date format. Use YYYY-MM-DD.",
        style=_style,
    ).ask()
    if start_date is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    # --- end_date ---
    end_date = questionary.text(
        "Enter end date (YYYY-MM-DD or 'today'):",
        default="today",
        validate=lambda val: _validate_date_or_today(val) or "Use YYYY-MM-DD or 'today'.",
        style=_style,
    ).ask()
    if end_date is None:
        raise KeyboardInterrupt("Prompt cancelled.")

    if end_date.lower() == "today":
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return {
        "exchange": exchange,
        "symbols": symbols,
        "time_horizon": time_horizon,
        "start_date": start_date,
        "end_date": end_date,
        "fill_missing_data": fill_missing_data,
        "retries": int(retries),
        "retry_delay": int(retry_delay),
    }


def run_with_config(config: dict) -> None:
    """Create a DataFetcher from *config* and download all selected symbols."""
    downloader = DataFetcher(config)
    downloader.download_all(config["symbols"])


# Validation helpers

def _validate_date(val: str) -> bool:
    try:
        datetime.strptime(val, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _validate_date_or_today(val: str) -> bool:
    if val.lower() == "today":
        return True
    return _validate_date(val)
