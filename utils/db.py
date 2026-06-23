"""
MarketLens - Database Schema
Defines per-symbol OHLCV tables for each exchange and handles table creation
against the binance_data and bybit_data PostgreSQL databases.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Float, TIMESTAMP, MetaData, Table


load_dotenv()  # reads .env from the project root

EXCHANGES = {
    "binance": {
        "host": os.getenv("BINANCE_DB_HOST", "localhost"),
        "port": os.getenv("BINANCE_DB_PORT", "5432"),
        "name": os.getenv("BINANCE_DB_NAME", "binance_data"),
        "user": os.getenv("BINANCE_DB_USER", ""),
        "password": os.getenv("BINANCE_DB_PASSWORD", ""),
    },
    "bybit": {
        "host": os.getenv("BYBIT_DB_HOST", "localhost"),
        "port": os.getenv("BYBIT_DB_PORT", "5432"),
        "name": os.getenv("BYBIT_DB_NAME", "bybit_data"),
        "user": os.getenv("BYBIT_DB_USER", ""),
        "password": os.getenv("BYBIT_DB_PASSWORD", ""),
    },
}

SYMBOLS = ["DOGE", "SOL", "BTC", "ETH", "ADA", "LTC", "MINA", "SUI"]

# Helpers

def _build_url(cfg: dict) -> str:
    """Build a PostgreSQL connection URL from a config dict."""
    return (
        f"postgresql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['name']}"
    )


def get_engine(exchange: str):
    """Return a SQLAlchemy engine for the given exchange.

    Parameters
    ----------
    exchange : str
        One of ``"binance"`` or ``"bybit"``.
    """
    if exchange not in EXCHANGES:
        raise ValueError(
            f"Unknown exchange '{exchange}'. Expected one of {list(EXCHANGES)}"
        )
    return create_engine(_build_url(EXCHANGES[exchange]))


def _define_tables(metadata: MetaData, exchange: str) -> list[Table]:
    """Define one OHLCV table per symbol for the given exchange.

    Table names follow the pattern ``<exchange>_<symbol_lower>``,
    e.g. ``binance_btc``, ``bybit_sol``.
    """
    tables = []
    for symbol in SYMBOLS:
        table_name = f"{exchange}_{symbol.lower()}"
        table = Table(
            table_name,
            metadata,
            Column("date_time", TIMESTAMP, primary_key=True),
            Column("open", Float),
            Column("high", Float),
            Column("low", Float),
            Column("close", Float),
            Column("volume", Float),
            extend_existing=True,
        )
        tables.append(table)
    return tables


# Public API

def create_all_tables() -> None:
    """Connect to both exchange databases and create all tables.

    Tables that already exist are silently skipped thanks to
    ``checkfirst=True`` (the default for ``metadata.create_all``).
    """
    for exchange, cfg in EXCHANGES.items():
        engine = create_engine(_build_url(cfg))
        metadata = MetaData()
        _define_tables(metadata, exchange)
        metadata.create_all(engine)
        engine.dispose()
        print(f"[✓] Tables ensured for '{exchange}' ({cfg['name']})")


if __name__ == "__main__":
    create_all_tables()
