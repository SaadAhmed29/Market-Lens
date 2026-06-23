"""
MarketLens - Schema Validation
Defines and validates the expected config schema for exchange configurations.
"""

from typing import Any

# Expected config keys and their types
EXPECTED_SCHEMA = {
    "exchange": str,
    "symbols": list,
    "time_horizon": str,
    "start_date": str,
    "end_date": str,
    "fill_missing_data": str,
    "retries": int,
    "retry_delay": int,
}

VALID_EXCHANGES = {"binance", "bybit"}

VALID_SYMBOLS = {"DOGE", "SOL", "BTC", "ETH", "ADA", "LTC", "MINA", "SUI"}

VALID_FILL_STRATEGIES = {"interpolation", "forward_fill", "drop"}


def validate_config(config: dict[str, Any]) -> list[str]:
    """Validate a loaded config dict against the expected schema.

    Returns a list of error messages. Empty list means valid.
    """
    # TODO: Check for missing keys
    # TODO: Validate value types against EXPECTED_SCHEMA
    # TODO: Validate exchange is in VALID_EXCHANGES
    # TODO: Validate symbols are in VALID_SYMBOLS
    # TODO: Validate date formats (YYYY-MM-DD or 'today')
    # TODO: Validate fill_missing_data is in VALID_FILL_STRATEGIES
    # TODO: Validate retries > 0 and retry_delay > 0
    return []
