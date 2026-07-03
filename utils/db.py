"""
MarketLens - Database Utilities
Defines per-symbol OHLCV tables for each exchange, handles table creation,
and provides helper functions for querying and inserting candle data.
"""

import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, Float, TIMESTAMP, MetaData, Table


load_dotenv()  # reads .env from the project root

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "name": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

SYMBOLS = ["DOGE", "SOL", "BTC", "ETH", "ADA", "LTC", "MINA", "SUI"]

# Connection helpers

def _build_url(cfg: dict) -> str:
    """Build a PostgreSQL connection URL from a config dict."""
    return (
        f"postgresql://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['name']}"
    )


def get_engine():
    """Return a SQLAlchemy engine for the database."""
    return create_engine(_build_url(DB_CONFIG))


# Data helpers

def table_name(exchange: str, symbol: str) -> str:
    """Return the DB table name for a given symbol, e.g. ``binance_data.btc_1m``."""
    return f"{exchange}_data.{symbol.lower()}_1m"


def get_table_name(symbol: str, timehorizon: str) -> str:
    """Return the formatted table name without schema, e.g. ``ada_1h``."""
    return f"{symbol.lower()}_{timehorizon}"


def create_table_if_not_exists(schema: str, table_name: str, engine) -> None:
    """Create an OHLCV table under the given schema if it doesn't already exist."""
    metadata = MetaData()
    table = Table(
        table_name,
        metadata,
        Column("date_time", TIMESTAMP(timezone=True), primary_key=True),
        Column("open", Float),
        Column("high", Float),
        Column("low", Float),
        Column("close", Float),
        Column("volume", Float),
        schema=schema,
        extend_existing=True,
    )
    metadata.create_all(engine, tables=[table])


def get_latest_datetime(engine, tbl_name: str) -> datetime | None:
    """Return the most recent ``date_time`` stored in *tbl_name*, or None."""
    query = text(f"SELECT MAX(date_time) FROM {tbl_name}")
    with engine.connect() as conn:
        result = conn.execute(query).scalar()
    return result


def get_earliest_datetime(engine, tbl_name: str) -> datetime | None:
    """Return the earliest ``date_time`` stored in *tbl_name*, or None."""
    query = text(f"SELECT MIN(date_time) FROM {tbl_name}")
    with engine.connect() as conn:
        result = conn.execute(query).scalar()
    return result


def insert_rows(engine, df: pd.DataFrame, tbl_name: str) -> int:
    """Insert DataFrame rows into *tbl_name*, silently skipping duplicates."""
    if df.empty:
        return 0

    insert_sql = text(
        f"INSERT INTO {tbl_name} "
        f"(date_time, open, high, low, close, volume) "
        f"VALUES (:date_time, :open, :high, :low, :close, :volume) "
        f"ON CONFLICT (date_time) DO NOTHING"
    )

    records = df.reset_index().to_dict("records")
    with engine.begin() as conn:
        conn.execute(insert_sql, records)

    return len(records)


def reorder_table(engine, tbl_name: str) -> None:
    """Physically reorder *tbl_name* rows by ``date_time`` using CLUSTER.

    This ensures that rows inserted out of chronological order (e.g. backfill)
    are stored on disk in the correct time sequence.
    """
    # tbl_name is "schema.table", e.g. "bybit_data.doge_1m"
    # The PK index name is "<table>_pkey"
    bare_table = tbl_name.split(".")[-1]
    index_name = f"{bare_table}_pkey"
    with engine.begin() as conn:
        conn.execute(text(f"CLUSTER {tbl_name} USING {index_name}"))


def _define_tables(metadata: MetaData, exchange: str) -> list[Table]:
    """Define one OHLCV table per symbol for the given exchange under its schema.

    Table names follow the pattern ``<symbol_lower>_1m``,
    e.g. ``btc_1m``, ``sol_1m``.
    """
    tables = []
    for symbol in SYMBOLS:
        table_name = f"{symbol.lower()}_1m"
        schema_name = f"{exchange}_data"
        table = Table(
            table_name,
            metadata,
            Column("date_time", TIMESTAMP(timezone=True), primary_key=True),
            Column("open", Float),
            Column("high", Float),
            Column("low", Float),
            Column("close", Float),
            Column("volume", Float),
            schema=schema_name,
            extend_existing=True,
        )
        tables.append(table)
    return tables


# Public API

def create_database_if_not_exists():
    """Create the database if it does not exist."""
    from sqlalchemy import text
    default_config = DB_CONFIG.copy()
    db_name = default_config["name"]
    default_config["name"] = "postgres"
    
    engine = create_engine(_build_url(default_config), isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
        if not result.fetchone():
            conn.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"[v] Created database '{db_name}'")
    engine.dispose()

def create_all_tables() -> None:
    """Connect to the database and create all schemas and tables.

    Tables that already exist are silently skipped thanks to
    ``checkfirst=True`` (the default for ``metadata.create_all``).
    """
    from sqlalchemy import text
    create_database_if_not_exists()
    
    engine = get_engine()
    metadata = MetaData()
    
    with engine.begin() as conn:
        for exchange in ["binance", "bybit"]:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {exchange}_data"))
            
    for exchange in ["binance", "bybit"]:
        _define_tables(metadata, exchange)
        
    metadata.create_all(engine)
    engine.dispose()
    print("[v] Schemas and tables ensured for both exchanges in Market-Lens database.")


if __name__ == "__main__":
    create_all_tables()
