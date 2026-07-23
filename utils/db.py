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
import numpy as np
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

def save_ledger(ledger_df: pd.DataFrame, strategy_name: str, if_exists: str = 'replace', schema: str = 'backtest_ledgers', table_suffix: str = '') -> None:
    """Save backtest ledger to the specified schema, replacing any existing table."""
    if ledger_df is None or ledger_df.empty:
        return
        
    engine = get_engine()
    table = f"{strategy_name.lower()}{table_suffix}"
    
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        # Add trade_id column to existing tables that don't have it yet
        conn.execute(text(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = '{schema}' AND table_name = '{table}'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = '{schema}' AND table_name = '{table}' AND column_name = 'trade_id'
                ) THEN
                    ALTER TABLE {schema}.{table} ADD COLUMN trade_id INTEGER;
                END IF;
            END $$;
        """))
        
    # Ensure columns are present and correctly named
    # entry_time, exit_time, direction, entry_price, exit_price, quantity, gross_pnl, commission, slippage, net_pnl, balance_after_trade
    # as well as exit_reason and forced_exit which are part of the ledger.
    ledger_df.to_sql(
        table,
        engine,
        schema=schema,
        if_exists=if_exists,
        index=False
    )
    print(f"[v] Saved ledger to {schema}.{table}")

def get_open_position(strategy_name: str) -> dict | None:
    """Retrieve the currently open position for the strategy, if any."""
    engine = get_engine()
    with engine.connect() as conn:
        try:
            row = conn.execute(
                text("SELECT * FROM simulation.positions WHERE strategy_name=:name AND status='Open' LIMIT 1"),
                {"name": strategy_name}
            ).mappings().fetchone()
            if row:
                d = dict(row)
                d['take_profit'] = d.pop('tp_price', None)
                d['stop_loss'] = d.pop('sl_price', None)
                return d
        except Exception:
            pass
    return None

def upsert_position(position_dict: dict, strategy_name: str) -> None:
    """Upsert the active position state into the {strategy_name}_positions table."""
    engine = get_engine()
    schema = 'backtest_ledgers'
    table = f"{strategy_name.lower()}_positions"
    
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {schema}.{table} (
                trade_id SERIAL PRIMARY KEY,
                direction TEXT,
                entry_time TIMESTAMP WITH TIME ZONE,
                entry_price FLOAT,
                quantity FLOAT,
                take_profit FLOAT,
                stop_loss FLOAT,
                current_price FLOAT,
                unrealized_pnl FLOAT,
                status TEXT
            )
        """))
        
        if "trade_id" in position_dict and position_dict["trade_id"] is not None:
            conn.execute(text(f"""
                UPDATE {schema}.{table}
                SET current_price = :current_price,
                    unrealized_pnl = :unrealized_pnl,
                    status = :status,
                    take_profit = :take_profit,
                    stop_loss = :stop_loss
                WHERE trade_id = :trade_id
            """), position_dict)
        else:
            conn.execute(text(f"UPDATE {schema}.{table} SET status='Closed' WHERE status='Open'"))
            conn.execute(text(f"""
                INSERT INTO {schema}.{table} 
                (direction, entry_time, entry_price, quantity, take_profit, stop_loss, current_price, unrealized_pnl, status)
                VALUES (:direction, :entry_time, :entry_price, :quantity, :take_profit, :stop_loss, :current_price, :unrealized_pnl, :status)
            """), position_dict)

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
    table = f"{strategy_name.lower()}"
    
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
    """Create the meta_data schema and new data_config table.
    
    Drops any existing data_config table and creates it with the new schema,
    seeding it with 1m timeframes for all symbols across both exchanges.
    """
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS meta_data"))
        conn.execute(text("DROP TABLE IF EXISTS meta_data.data_config CASCADE"))
        
        conn.execute(text("""
            CREATE TABLE meta_data.data_config (
                id            SERIAL PRIMARY KEY,
                exchange      TEXT NOT NULL,
                symbol        TEXT NOT NULL,
                time_horizon  TEXT NOT NULL,
                records_count INTEGER DEFAULT 0,
                start_date    TIMESTAMP,
                end_date      TIMESTAMP,
                UNIQUE (exchange, symbol, time_horizon)
            )
        """))

        # Seed with 1m combinations for 8 symbols across both exchanges (16 rows)
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc)
        start_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
        
        conn.execute(text("""
            INSERT INTO meta_data.data_config
                (exchange, symbol, time_horizon, start_date, end_date)
            SELECT 
                e.exchange, 
                s.symbol, 
                '1m',
                :start_dt,
                :end_dt
            FROM 
                UNNEST(ARRAY['binance', 'bybit']) AS e(exchange)
            CROSS JOIN 
                UNNEST(ARRAY['BTC', 'ETH', 'SOL', 'DOGE', 'ADA', 'LTC', 'MINA', 'SUI']) AS s(symbol)
            ON CONFLICT DO NOTHING
        """), {"start_dt": start_dt, "end_dt": today})

    print("[v] meta_data schema and data_config table ensured with new schema.")


def load_data_config(exchange: str) -> list[dict]:
    """Fetch all rows for the given exchange from data_config and return as list of dicts."""
    engine = get_engine()

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT symbol, time_horizon, start_date, end_date, records_count
                FROM meta_data.data_config
                WHERE exchange = :exchange
            """),
            {"exchange": exchange}
        ).mappings().fetchall()

    return [dict(row) for row in rows]

def update_data_config_dates(exchange: str, symbol: str, time_horizon: str, start_date, end_date) -> None:
    """Updates the start_date, end_date, and records_count for a matching row."""
    engine = get_engine()
    
    # Calculate records count dynamically based on the actual table
    bare_tbl = get_table_name(symbol, time_horizon)
    tbl_name = f"{exchange}_data.{bare_tbl}"
    
    with engine.begin() as conn:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {tbl_name}")).scalar()
        except Exception:
            count = 0
            
        conn.execute(
            text("""
                UPDATE meta_data.data_config
                SET start_date = :start_date,
                    end_date = :end_date,
                    records_count = :count
                WHERE exchange = :exchange
                  AND symbol = :symbol
                  AND time_horizon = :time_horizon
            """),
            {
                "start_date": start_date,
                "end_date": end_date,
                "count": count,
                "exchange": exchange,
                "symbol": symbol,
                "time_horizon": time_horizon
            }
        )


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


def load_strategies_config() -> list[dict]:
    engine = get_engine()
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT strategy_name, config FROM meta_data.strategies")).mappings().all()
    
    return [dict(row) for row in rows]


def create_backtest_config_table() -> None:
    """Create and seed the meta_data.backtest_config table if it doesn't exist."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS meta_data"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meta_data.backtest_config (
                strategy_id INTEGER PRIMARY KEY REFERENCES meta_data.strategies(id),
                config JSONB
            )
        """))

        row_count = conn.execute(text("SELECT COUNT(*) FROM meta_data.backtest_config")).scalar()
        if row_count == 0:
            default_config = {
                "initial_balance": 10000.0,
                "exit_on_opposite_signal": True,
                "position_size": {"type": "fixed_percentage", "value": 10},
                "commission": 0.05,
                "slippage": 0.02,
                "allow_long": True,
                "allow_short": True,
                "take_profit": {"enabled": True, "type": "percentage", "value": 1.0},
                "stop_loss": {"enabled": True, "type": "percentage", "value": 0.75},
                "entry_price": {"method": "next_open"},
                "exit_price": {"method": "next_open"},
                "max_open_positions": 1
            }

            strategy_ids = conn.execute(text("SELECT id FROM meta_data.strategies")).scalars().all()

            for strategy_id in strategy_ids:
                conn.execute(text("""
                    INSERT INTO meta_data.backtest_config (strategy_id, config)
                    VALUES (:strategy_id, :config)
                """), {
                    "strategy_id": strategy_id,
                    "config": json.dumps(default_config)
                })
            print("[v] Seeded meta_data.backtest_config with default values.")


def load_backtest_config() -> dict:
    """Fetch all backtest_config rows and return them as a dict keyed by strategy_id."""
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT strategy_id, config FROM meta_data.backtest_config")).mappings().fetchall()

    config = {}
    for row in rows:
        config[row["strategy_id"]] = row["config"]
    return config

_cli_style = Style([
    ('qmark', 'fg:#673ab7 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#f44336 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
])

def load_db_config() -> dict:
    """Fetch the config from meta_data.data_config and return it as a dict.
    Provides fallback defaults for CLI options no longer in the DB.
    """
    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT 
                    array_agg(DISTINCT exchange) as exchange,
                    array_agg(DISTINCT symbol) as symbols,
                    array_agg(DISTINCT time_horizon) as time_horizons
                FROM meta_data.data_config
            """)
        ).mappings().fetchone()

    if row is None or not row["exchange"]:
        raise RuntimeError(
            "meta_data.data_config is empty. "
            "Run create_meta_data_schema() first to seed defaults."
        )

    return {
        "exchange": list(row["exchange"]),
        "symbols": list(row["symbols"]),
        "time_horizons": list(row["time_horizons"]),
        "fill_missing_data": ['interpolation', 'forward_fill', 'backward_fill', 'zero_fill', 'drop'],
        "retries": [1, 2, 3, 5, 10],
        "retry_delay": [1, 2, 5, 10, 30],
    }


def run_cli(options: list[str], preset_exchange: str | None = None,
            multi_select_options: list[dict] | None = None) -> dict:
    """
    Run interactive CLI prompts for the fields specified in `options`.
    Returns a dict with the selected values.

    Parameters
    ----------
    multi_select_options : list[dict], optional
        Each dict must have ``key`` (result key), ``prompt`` (question text),
        and ``choices`` (list of strings).  Presented as checkbox prompts.
    """
    from datetime import datetime, timezone
    
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
        result['strategy_id'] = selected_row['id']

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
            result['symbols'] = [sym] # Keep as list for consistency but with one element
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
    if 'timehorizon' in options:
        th = questionary.select(
            "Select time horizon:",
            choices=db_config["time_horizons"],
            style=_cli_style,
        ).ask()
        if th is None:
            raise KeyboardInterrupt("Prompt cancelled.")
        result['timehorizon'] = th

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

    # --- multi_select ---
    if multi_select_options:
        for ms in multi_select_options:
            selections = questionary.checkbox(
                ms["prompt"],
                choices=ms["choices"],
                style=_cli_style,
                validate=lambda sel: len(sel) > 0 or "Select at least one option.",
            ).ask()
            if selections is None:
                raise KeyboardInterrupt("Prompt cancelled.")
            result[ms["key"]] = selections

    return result

def create_simulation_schema() -> None:
    """Create simulation schema and its tables."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS simulation"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS simulation.positions (
                trade_id INTEGER,
                strategy_name TEXT PRIMARY KEY,
                entry_time TIMESTAMP WITH TIME ZONE,
                direction TEXT,
                entry_price FLOAT,
                quantity FLOAT,
                tp_price FLOAT,
                sl_price FLOAT,
                current_price FLOAT,
                unrealized_pnl FLOAT,
                status TEXT
            )
        """))
        # Add missing columns if table already exists without them
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'simulation' AND table_name = 'positions' AND column_name = 'trade_id'
                ) THEN
                    ALTER TABLE simulation.positions ADD COLUMN trade_id INTEGER;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'simulation' AND table_name = 'positions' AND column_name = 'current_price'
                ) THEN
                    ALTER TABLE simulation.positions ADD COLUMN current_price FLOAT;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'simulation' AND table_name = 'positions' AND column_name = 'unrealized_pnl'
                ) THEN
                    ALTER TABLE simulation.positions ADD COLUMN unrealized_pnl FLOAT;
                END IF;
            END $$;
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS simulation.stats (
                strategy_name TEXT PRIMARY KEY,
                final_balance FLOAT,
                total_trades INTEGER,
                sharpe_ratio FLOAT,
                sortino_ratio FLOAT,
                calmar_ratio FLOAT,
                max_drawdown FLOAT,
                cagr FLOAT,
                volatility FLOAT,
                win_rate FLOAT,
                profit_factor FLOAT,
                average_win FLOAT,
                average_loss FLOAT,
                best_day FLOAT,
                worst_day FLOAT,
                var FLOAT,
                cvar FLOAT,
                skewness FLOAT,
                kurtosis FLOAT,
                recovery_factor FLOAT,
                ulcer_index FLOAT,
                avg_return FLOAT,
                common_sense_ratio FLOAT,
                comp FLOAT,
                conditional_value_at_risk FLOAT,
                consecutive_losses INTEGER,
                consecutive_wins INTEGER,
                cpc_index FLOAT,
                expected_return FLOAT,
                expected_shortfall FLOAT,
                exposure FLOAT,
                gain_to_pain_ratio FLOAT,
                geometric_mean FLOAT,
                ghpr FLOAT,
                outlier_loss_ratio FLOAT,
                outlier_win_ratio FLOAT,
                payoff_ratio FLOAT,
                profit_ratio FLOAT,
                rar FLOAT,
                risk_of_ruin FLOAT,
                ror FLOAT,
                tail_ratio FLOAT,
                ulcer_performance_index FLOAT,
                upi FLOAT,
                win_loss_ratio FLOAT,
                kelly_criterion FLOAT,
                risk_return_ratio FLOAT
            )
        """))
    print("[v] simulation schema and tables ensured.")

def upsert_simulation_position(strategy_name: str, position_data: dict) -> None:
    """Upsert a single position row for the strategy in simulation.positions."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO simulation.positions (
                strategy_name, trade_id, entry_time, direction, entry_price, quantity, tp_price, sl_price, current_price, unrealized_pnl, status
            ) VALUES (
                :strategy_name, :trade_id, :entry_time, :direction, :entry_price, :quantity, :tp_price, :sl_price, :current_price, :unrealized_pnl, :status
            ) ON CONFLICT (strategy_name) DO UPDATE SET
                trade_id = EXCLUDED.trade_id,
                entry_time = EXCLUDED.entry_time,
                direction = EXCLUDED.direction,
                entry_price = EXCLUDED.entry_price,
                quantity = EXCLUDED.quantity,
                tp_price = EXCLUDED.tp_price,
                sl_price = EXCLUDED.sl_price,
                current_price = EXCLUDED.current_price,
                unrealized_pnl = EXCLUDED.unrealized_pnl,
                status = EXCLUDED.status
        """), {
            "strategy_name": strategy_name,
            **position_data
        })

def upsert_simulation_stats(strategy_name: str, stats_data: dict) -> None:
    """Upsert a single stats row for the strategy in simulation.stats."""
    engine = get_engine()

    columns = [
        "final_balance", "total_trades", "sharpe_ratio", "sortino_ratio",
        "calmar_ratio", "max_drawdown", "cagr", "volatility", "win_rate",
        "profit_factor", "average_win", "average_loss", "best_day", "worst_day",
        "var", "cvar", "skewness", "kurtosis", "recovery_factor", "ulcer_index",
        "avg_return", "common_sense_ratio", "comp", "conditional_value_at_risk",
        "consecutive_losses", "consecutive_wins", "cpc_index", "expected_return",
        "expected_shortfall", "exposure", "gain_to_pain_ratio", "geometric_mean",
        "ghpr", "outlier_loss_ratio", "outlier_win_ratio", "payoff_ratio",
        "profit_ratio", "rar", "risk_of_ruin", "ror", "tail_ratio",
        "ulcer_performance_index", "upi", "win_loss_ratio", "kelly_criterion",
        "risk_return_ratio",
    ]

    insert_cols = ", ".join(["strategy_name"] + columns)
    insert_placeholders = ", ".join([":strategy_name"] + [f":{c}" for c in columns])
    update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in columns])

    query = text(f"""
        INSERT INTO simulation.stats (
            {insert_cols}
        ) VALUES (
            {insert_placeholders}
        ) ON CONFLICT (strategy_name) DO UPDATE SET
            {update_clause}
    """)

    params = {"strategy_name": strategy_name}
    for c in columns:
        val = stats_data.get(c)
        if isinstance(val, (np.floating, np.integer)):
            val = val.item()
        params[c] = val

    with engine.begin() as conn:
        conn.execute(query, params)



def create_execution_schema() -> None:
    """Create execution schema, execution_ledgers schema and their tables."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS execution"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS execution_ledgers"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS execution.positions (
                strategy_name TEXT PRIMARY KEY,
                order_id TEXT,
                entry_time TIMESTAMP WITH TIME ZONE,
                direction TEXT,
                entry_price FLOAT,
                quantity FLOAT,
                tp_price FLOAT,
                sl_price FLOAT,
                status TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS execution.stats (
                strategy_name TEXT PRIMARY KEY,
                final_balance FLOAT,
                total_trades INTEGER,
                sharpe_ratio FLOAT,
                sortino_ratio FLOAT,
                calmar_ratio FLOAT,
                max_drawdown FLOAT,
                cagr FLOAT,
                volatility FLOAT,
                win_rate FLOAT,
                profit_factor FLOAT,
                average_win FLOAT,
                average_loss FLOAT,
                best_day FLOAT,
                worst_day FLOAT,
                var FLOAT,
                cvar FLOAT,
                skewness FLOAT,
                kurtosis FLOAT,
                recovery_factor FLOAT,
                ulcer_index FLOAT,
                avg_return FLOAT,
                common_sense_ratio FLOAT,
                comp FLOAT,
                conditional_value_at_risk FLOAT,
                consecutive_losses INTEGER,
                consecutive_wins INTEGER,
                cpc_index FLOAT,
                expected_return FLOAT,
                expected_shortfall FLOAT,
                exposure FLOAT,
                gain_to_pain_ratio FLOAT,
                geometric_mean FLOAT,
                ghpr FLOAT,
                outlier_loss_ratio FLOAT,
                outlier_win_ratio FLOAT,
                payoff_ratio FLOAT,
                profit_ratio FLOAT,
                rar FLOAT,
                risk_of_ruin FLOAT,
                ror FLOAT,
                tail_ratio FLOAT,
                ulcer_performance_index FLOAT,
                upi FLOAT,
                win_loss_ratio FLOAT,
                kelly_criterion FLOAT,
                risk_return_ratio FLOAT
            )
        """))
    print("[v] execution schema and tables ensured.")

def upsert_execution_position(strategy_name: str, position_data: dict) -> None:
    """Upsert a single position row for the strategy in execution.positions."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO execution.positions (
                strategy_name, order_id, entry_time, direction, entry_price, quantity, tp_price, sl_price, status
            ) VALUES (
                :strategy_name, :order_id, :entry_time, :direction, :entry_price, :quantity, :tp_price, :sl_price, :status
            ) ON CONFLICT (strategy_name) DO UPDATE SET
                order_id = EXCLUDED.order_id,
                entry_time = EXCLUDED.entry_time,
                direction = EXCLUDED.direction,
                entry_price = EXCLUDED.entry_price,
                quantity = EXCLUDED.quantity,
                tp_price = EXCLUDED.tp_price,
                sl_price = EXCLUDED.sl_price,
                status = EXCLUDED.status
        """), {
            "strategy_name": strategy_name,
            **position_data
        })

def upsert_execution_stats(strategy_name: str, stats_data: dict) -> None:
    """Upsert a single stats row for the strategy in execution.stats."""
    engine = get_engine()

    columns = [
        "final_balance", "total_trades", "sharpe_ratio", "sortino_ratio",
        "calmar_ratio", "max_drawdown", "cagr", "volatility", "win_rate",
        "profit_factor", "average_win", "average_loss", "best_day", "worst_day",
        "var", "cvar", "skewness", "kurtosis", "recovery_factor", "ulcer_index",
        "avg_return", "common_sense_ratio", "comp", "conditional_value_at_risk",
        "consecutive_losses", "consecutive_wins", "cpc_index", "expected_return",
        "expected_shortfall", "exposure", "gain_to_pain_ratio", "geometric_mean",
        "ghpr", "outlier_loss_ratio", "outlier_win_ratio", "payoff_ratio",
        "profit_ratio", "rar", "risk_of_ruin", "ror", "tail_ratio",
        "ulcer_performance_index", "upi", "win_loss_ratio", "kelly_criterion",
        "risk_return_ratio",
    ]

    insert_cols = ", ".join(["strategy_name"] + columns)
    insert_placeholders = ", ".join([":strategy_name"] + [f":{c}" for c in columns])
    update_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in columns])

    query = text(f"""
        INSERT INTO execution.stats (
            {insert_cols}
        ) VALUES (
            {insert_placeholders}
        ) ON CONFLICT (strategy_name) DO UPDATE SET
            {update_clause}
    """)

    params = {"strategy_name": strategy_name}
    for c in columns:
        val = stats_data.get(c)
        if isinstance(val, (np.floating, np.integer)):
            val = val.item()
        params[c] = val

    with engine.begin() as conn:
        conn.execute(query, params)


# Accounts schema

def create_accounts_schema() -> None:
    """Create the accounts schema and the api table.

    Seeds the first row from .env (BYBIT_API_KEY / BYBIT_API_SECRET) when the
    table is empty so existing single-account setups keep working.
    """
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS accounts"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS accounts.api (
                account_name   TEXT PRIMARY KEY,
                bybit_api_key  TEXT NOT NULL,
                bybit_api_secret TEXT NOT NULL
            )
        """))

        row_count = conn.execute(text("SELECT COUNT(*) FROM accounts.api")).scalar()
        if row_count == 0:
            key = os.getenv("BYBIT_API_KEY", "")
            secret = os.getenv("BYBIT_API_SECRET", "")
            if key and secret:
                conn.execute(text("""
                    INSERT INTO accounts.api (account_name, bybit_api_key, bybit_api_secret)
                    VALUES (:name, :key, :secret)
                    ON CONFLICT DO NOTHING
                """), {"name": "main", "key": key, "secret": secret})
    print("[v] accounts schema and api table ensured.")


def create_account_history_table(account_name: str) -> None:
    """Create accounts.{account_name}_history for raw Bybit execution records."""
    table = f"{account_name.lower()}_history"
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS accounts"))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS accounts.{table} (
                exec_id    TEXT PRIMARY KEY,
                order_id   TEXT,
                symbol     TEXT,
                side       TEXT,
                price      FLOAT,
                qty        FLOAT,
                fee        FLOAT,
                fee_rate   FLOAT,
                exec_time  TIMESTAMP WITH TIME ZONE,
                order_type TEXT,
                is_maker   BOOLEAN
            )
        """))


def create_account_stats_table(account_name: str) -> None:
    """Create accounts.{account_name}_stats as a single-row stats store."""
    table = f"{account_name.lower()}_stats"
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS accounts"))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS accounts.{table} (
                id                       INTEGER PRIMARY KEY DEFAULT 1,
                last_updated             TIMESTAMP WITH TIME ZONE,
                -- closed PnL stats
                total_realized_pnl       FLOAT,
                win_rate                 FLOAT,
                avg_win                  FLOAT,
                avg_loss                 FLOAT,
                largest_win              FLOAT,
                largest_loss             FLOAT,
                profit_factor            FLOAT,
                expectancy               FLOAT,
                max_win_streak           INTEGER,
                max_loss_streak          INTEGER,
                avg_holding_time_seconds FLOAT,
                trades_per_day           FLOAT,
                pnl_by_symbol            JSONB,
                pnl_by_side              JSONB,
                pnl_by_hour              JSONB,
                pnl_by_dow               JSONB,
                -- execution stats
                total_fees_paid          FLOAT,
                total_volume_traded      FLOAT,
                fees_pct_of_volume       FLOAT,
                avg_trade_size           FLOAT,
                maker_fill_ratio         FLOAT,
                taker_fill_ratio         FLOAT,
                real_slippage_avg        FLOAT,
                -- order stats
                fill_rate                FLOAT,
                order_status_breakdown   JSONB,
                order_type_breakdown     JSONB,
                -- live snapshot
                open_position_count      INTEGER,
                total_notional_exposure  FLOAT,
                total_unrealized_pnl     FLOAT,
                wallet_balance           FLOAT,
                available_balance        FLOAT
            )
        """))


def load_api_credentials() -> list[dict]:
    """Return all rows from accounts.api as a list of dicts."""
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT account_name, bybit_api_key, bybit_api_secret FROM accounts.api")
        ).mappings().fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    create_all_tables()

