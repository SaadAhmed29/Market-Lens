"""
MarketLens - Database Utilities
Defines per-symbol OHLCV tables for each exchange, handles table creation,
and provides helper functions for querying and inserting candle data.
"""

import os
from datetime import datetime

import json
import yaml
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, Float, TIMESTAMP, MetaData, Table

import questionary
from questionary import Style


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

def save_ledger(ledger_df: pd.DataFrame, strategy_name: str) -> None:
    """Save backtest ledger to the backtest_ledgers schema, replacing any existing table."""
    if ledger_df is None or ledger_df.empty:
        return
        
    engine = get_engine()
    schema = 'backtest_ledgers'
    table = f"{strategy_name.lower()}_ledger"
    
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        
    # Ensure columns are present and correctly named
    # The columns match the requested full descriptive names with underscores:
    # entry_time, exit_time, direction, entry_price, exit_price, quantity, gross_pnl, commission, slippage, net_pnl, balance_after_trade
    # as well as exit_reason and forced_exit which are part of the ledger.
    ledger_df.to_sql(
        table,
        engine,
        schema=schema,
        if_exists='replace',
        index=False
    )
    print(f"[v] Saved ledger to {schema}.{table}")

def create_signal_schema() -> None:
    """Create the signal schema if it does not exist."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS signal"))
    print("[v] signal schema ensured.")

def save_signals(signal_df: pd.DataFrame, strategy_name: str) -> None:
    """Save signal dataframe to the signal schema, replacing any existing table."""
    if signal_df is None or signal_df.empty:
        return
        
    engine = get_engine()
    schema = 'signal'
    table = f"{strategy_name.lower()}_signal"
    
    signal_col = 'signal' if 'signal' in signal_df.columns else signal_df.columns[0]
    df_to_save = signal_df[[signal_col]].copy()
    df_to_save = df_to_save.rename(columns={signal_col: 'signal'})
    df_to_save.index.name = 'date_time'
    
    df_to_save.to_sql(
        table,
        engine,
        schema=schema,
        if_exists='replace',
        index=True
    )
    print(f"[v] Saved signals to {schema}.{table}")

def create_meta_data_schema() -> None:
    """Create the meta_data schema and data_config table with sensible defaults.

    The table stores arrays of allowed options for each config variable.
    A default row is inserted only if the table is empty (first run).
    """
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS meta_data"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meta_data.data_config (
                exchange          TEXT[]    NOT NULL,
                symbols           TEXT[]    NOT NULL,
                time_horizons     TEXT[]    NOT NULL,
                fill_missing_data TEXT[]    NOT NULL,
                retries           INTEGER[] NOT NULL,
                retry_delay       INTEGER[] NOT NULL
            )
        """))

        # Insert default row only if table is empty
        row_count = conn.execute(
            text("SELECT COUNT(*) FROM meta_data.data_config")
        ).scalar()

        if row_count == 0:
            conn.execute(text("""
                INSERT INTO meta_data.data_config
                    (exchange, symbols, time_horizons, fill_missing_data, retries, retry_delay)
                VALUES (
                    ARRAY['binance', 'bybit'],
                    ARRAY['BTC', 'ETH', 'SOL', 'DOGE', 'ADA', 'LTC', 'MINA', 'SUI'],
                    ARRAY['1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d'],
                    ARRAY['interpolation', 'forward_fill', 'backward_fill', 'zero_fill', 'drop'],
                    ARRAY[1, 2, 3, 5, 10],
                    ARRAY[1, 2, 5, 10, 30]
                )
            """))
            print("[v] Inserted default row into meta_data.data_config")

    print("[v] meta_data schema and data_config table ensured.")


def load_db_config() -> dict:
    """Fetch the single row from meta_data.data_config and return it as a dict."""
    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM meta_data.data_config LIMIT 1")
        ).mappings().fetchone()

    if row is None:
        raise RuntimeError(
            "meta_data.data_config is empty. "
            "Run create_meta_data_schema() first to seed defaults."
        )

    return {
        "exchange": list(row["exchange"]),
        "symbols": list(row["symbols"]),
        "time_horizons": list(row["time_horizons"]),
        "fill_missing_data": list(row["fill_missing_data"]),
        "retries": list(row["retries"]),
        "retry_delay": list(row["retry_delay"]),
    }


def create_strategy_table() -> None:
    """Create the meta_data.strategies table if it does not exist."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS meta_data"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meta_data.strategies (
                id            SERIAL PRIMARY KEY,
                strategy_name TEXT NOT NULL,
                config        JSONB NOT NULL
            )
        """))
    print("[v] meta_data.strategies table ensured.")


def seed_strategies() -> None:
    """Read signals/config.yaml and seed the strategies table if empty."""
    create_strategy_table()
    engine = get_engine()
    
    with engine.begin() as conn:
        row_count = conn.execute(text("SELECT COUNT(*) FROM meta_data.strategies")).scalar()
        if row_count > 0:
            return  # Already seeded
            
        try:
            with open("signals/config.yaml", "r") as f:
                strategies = yaml.safe_load(f)
                
            if not strategies:
                return
                
            for name, cfg in strategies.items():
                conn.execute(
                    text("INSERT INTO meta_data.strategies (strategy_name, config) VALUES (:name, :config)"),
                    {"name": name, "config": json.dumps(cfg)}
                )
            print(f"[v] Seeded {len(strategies)} strategies into meta_data.strategies.")
        except FileNotFoundError:
            print("[!] signals/config.yaml not found, skipping strategy seeding.")


# Styling for the CLI prompts
_cli_style = Style([
    ("qmark", "fg:cyan bold"),
    ("question", "fg:white bold"),
    ("answer", "fg:green bold"),
    ("pointer", "fg:cyan bold"),
    ("highlighted", "fg:cyan bold"),
    ("selected", "fg:green"),
])

def run_cli(options: list[str], preset_exchange: str | None = None) -> dict:
    """
    Run interactive CLI prompts for the fields specified in `options`.
    Returns a dict with the selected values.
    """
    from datetime import datetime, timezone
    
    create_meta_data_schema()
    db_config = load_db_config()
    
    result = {}
    
    # --- strategy ---
    if 'strategy' in options:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, strategy_name, config FROM meta_data.strategies ORDER BY id")).mappings().fetchall()
            
        if not rows:
            print("[!] No strategies found in DB.")
            raise KeyboardInterrupt("Prompt cancelled.")
            
        choices = [f"{r['id']} - {r['strategy_name']}" for r in rows]
        strategy_selection = questionary.select(
            "Select strategy:",
            choices=choices,
            style=_cli_style,
        ).ask()
        if strategy_selection is None:
            raise KeyboardInterrupt("Prompt cancelled.")
            
        selected_id = int(strategy_selection.split(" - ")[0])
        selected_row = next(r for r in rows if r['id'] == selected_id)
        
        result['strategy_name'] = selected_row['strategy_name']
        result['strategy_config'] = selected_row['config']

    # --- exchange ---
    if 'exchange' in options:
        if preset_exchange:
            result['exchange'] = preset_exchange
            print(f"Exchange: {preset_exchange}")
        else:
            exch = questionary.select(
                "Select exchange:",
                choices=db_config["exchange"],
                style=_cli_style,
            ).ask()
            if exch is None:
                raise KeyboardInterrupt("Prompt cancelled.")
            result['exchange'] = exch

    # --- symbols ---
    if 'symbols' in options:
        # If 'strategy' is in options, we use single-select (as per user request: calculate for one symbol only)
        if 'strategy' in options:
            sym = questionary.select(
                "Select symbol:",
                choices=db_config["symbols"],
                style=_cli_style,
            ).ask()
            if sym is None:
                raise KeyboardInterrupt("Prompt cancelled.")
            # We return a list with one item so it's compatible or just the string if appropriate.
            # We'll return the string since the user said "single symbol"
            result['symbols'] = [sym] # Keep as list for consistency but with one element, wait, user said "only one symbol". Let's use string.
        else:
            syms = questionary.checkbox(
                "Select symbols:",
                choices=db_config["symbols"],
                style=_cli_style,
                validate=lambda sel: len(sel) > 0 or "Select at least one symbol.",
            ).ask()
            if syms is None:
                raise KeyboardInterrupt("Prompt cancelled.")
            result['symbols'] = syms

    # --- time_horizon ---
    if 'time_horizon' in options:
        th = questionary.select(
            "Select time horizon:",
            choices=db_config["time_horizons"],
            style=_cli_style,
        ).ask()
        if th is None:
            raise KeyboardInterrupt("Prompt cancelled.")
        result['time_horizon'] = th

    # --- fill_missing_data ---
    if 'fill_missing_data' in options:
        fmd = questionary.select(
            "Select fill strategy for missing data:",
            choices=db_config["fill_missing_data"],
            style=_cli_style,
        ).ask()
        if fmd is None:
            raise KeyboardInterrupt("Prompt cancelled.")
        result['fill_missing_data'] = fmd

    # --- retries ---
    if 'retries' in options:
        r = questionary.select(
            "Select number of retries:",
            choices=[str(x) for x in db_config["retries"]],
            style=_cli_style,
        ).ask()
        if r is None:
            raise KeyboardInterrupt("Prompt cancelled.")
        result['retries'] = int(r)

    # --- retry_delay ---
    if 'retry_delay' in options:
        rd = questionary.select(
            "Select retry delay (seconds):",
            choices=[str(x) for x in db_config["retry_delay"]],
            style=_cli_style,
        ).ask()
        if rd is None:
            raise KeyboardInterrupt("Prompt cancelled.")
        result['retry_delay'] = int(rd)

    # --- start_date ---
    def _validate_date(val: str) -> bool:
        try:
            datetime.strptime(val, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    if 'start_date' in options:
        sd = questionary.text(
            "Enter start date (YYYY-MM-DD):",
            validate=lambda val: _validate_date(val) or "Invalid date format. Use YYYY-MM-DD.",
            style=_cli_style,
        ).ask()
        if sd is None:
            raise KeyboardInterrupt("Prompt cancelled.")
        result['start_date'] = sd

    # --- end_date ---
    def _validate_date_or_today(val: str) -> bool:
        if val.lower() == "today":
            return True
        return _validate_date(val)

    if 'end_date' in options:
        ed = questionary.text(
            "Enter end date (YYYY-MM-DD or 'today'):",
            default="today",
            validate=lambda val: _validate_date_or_today(val) or "Use YYYY-MM-DD or 'today'.",
            style=_cli_style,
        ).ask()
        if ed is None:
            raise KeyboardInterrupt("Prompt cancelled.")
        if ed.lower() == "today":
            ed = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        result['end_date'] = ed

    return result


if __name__ == "__main__":
    create_all_tables()

