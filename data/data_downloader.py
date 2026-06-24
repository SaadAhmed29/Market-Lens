"""
MarketLens - Data Downloader
Fetches OHLCV candle data from Binance and Bybit APIs.
Supports incremental updates, retry logic, and missing-data interpolation.
"""

import time
import logging
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text

from utils.db import get_engine

logger = logging.getLogger(__name__)

# Mapping: config time_horizon → Binance interval string
BINANCE_INTERVALS = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
    "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M",
}

# Mapping: config time_horizon → Bybit interval string
BYBIT_INTERVALS = {
    "1m": "1", "3m": "3", "5m": "5", "15m": "15", "30m": "30",
    "1h": "60", "2h": "120", "4h": "240", "6h": "360", "12h": "720",
    "1d": "D", "1w": "W", "1M": "M",
}

# Mapping: config time_horizon → pandas frequency for resampling / gap detection
PANDAS_FREQ = {
    "1m": "1min", "3m": "3min", "5m": "5min", "15m": "15min", "30m": "30min",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
    "1d": "1D", "3d": "3D", "1w": "1W", "1M": "1ME",
}

# Mapping: config time_horizon → timedelta for offset calculations
INTERVAL_DELTAS = {
    "1m": timedelta(minutes=1), "3m": timedelta(minutes=3),
    "5m": timedelta(minutes=5), "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30), "1h": timedelta(hours=1),
    "2h": timedelta(hours=2), "4h": timedelta(hours=4),
    "6h": timedelta(hours=6), "8h": timedelta(hours=8),
    "12h": timedelta(hours=12), "1d": timedelta(days=1),
    "3d": timedelta(days=3), "1w": timedelta(weeks=1),
    "1M": timedelta(days=30),
}


class DataFetcher:
    """Downloads OHLCV market data from exchange APIs with retry logic,
    incremental updates, and configurable missing-data handling."""

    def __init__(self, config: dict) -> None:
        self.exchange = config["exchange"]
        self.time_horizon = config["time_horizon"]
        self.start_date = config["start_date"]
        self.end_date = config["end_date"]
        self.fill_strategy = config.get("fill_missing_data", "interpolation")
        self.retries = config.get("retries", 3)
        self.retry_delay = config.get("retry_delay", 5)

        self.engine = get_engine(self.exchange)
        self._client = None  # lazily initialised

    # Client initialisation

    def _get_client(self):
        """Lazily initialise the exchange API client."""
        if self._client is not None:
            return self._client

        if self.exchange == "binance":
            from binance.client import Client
            self._client = Client("", "")  # public data — no keys needed
        elif self.exchange == "bybit":
            from pybit.unified_trading import HTTP
            self._client = HTTP(testnet=False)
        else:
            raise ValueError(f"Unsupported exchange: {self.exchange}")

        return self._client

    # Database helpers

    def _table_name(self, symbol: str) -> str:
        """Return the DB table name for a given symbol, e.g. ``binance_btc``."""
        return f"{self.exchange}_{symbol.lower()}"

    def _get_latest_datetime(self, table_name: str) -> datetime | None:
        """Return the most recent ``date_time`` stored in *table_name*, or None."""
        query = text(f"SELECT MAX(date_time) FROM {table_name}")
        with self.engine.connect() as conn:
            result = conn.execute(query).scalar()
        return result

    def _insert_rows(self, df: pd.DataFrame, table_name: str) -> int:
        """Insert DataFrame rows into *table_name*, silently skipping duplicates."""
        if df.empty:
            return 0

        insert_sql = text(
            f"INSERT INTO {table_name} "
            f"(date_time, open, high, low, close, volume) "
            f"VALUES (:date_time, :open, :high, :low, :close, :volume) "
            f"ON CONFLICT (date_time) DO NOTHING"
        )

        records = df.reset_index().to_dict("records")
        with self.engine.begin() as conn:
            conn.execute(insert_sql, records)

        return len(records)

    # Fetch: Binance

    def _fetch_binance(self, symbol: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
        """Fetch OHLCV candles from Binance via ``get_historical_klines``."""
        client = self._get_client()
        interval = BINANCE_INTERVALS.get(self.time_horizon)
        if interval is None:
            raise ValueError(f"Unsupported time_horizon for Binance: {self.time_horizon}")

        api_symbol = f"{symbol}USDT"
        start_str = start_dt.strftime("%d %b, %Y")
        end_str = end_dt.strftime("%d %b, %Y")

        klines = client.get_historical_klines(
            symbol=api_symbol,
            interval=interval,
            start_str=start_str,
            end_str=end_str,
        )

        if not klines:
            return pd.DataFrame()

        # kline layout: [OpenTime, Open, High, Low, Close, Volume, ...]
        records = []
        for k in klines:
            records.append({
                "date_time": datetime.utcfromtimestamp(k[0] / 1000),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            })

        df = pd.DataFrame(records)
        df.set_index("date_time", inplace=True)
        df.sort_index(inplace=True)
        return df

    # Fetch: Bybit

    def _fetch_bybit(self, symbol: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
        """Fetch OHLCV candles from Bybit via ``get_kline``, with pagination."""
        client = self._get_client()
        interval = BYBIT_INTERVALS.get(self.time_horizon)
        if interval is None:
            raise ValueError(f"Unsupported time_horizon for Bybit: {self.time_horizon}")

        api_symbol = f"{symbol}USDT"
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        delta_ms = int(INTERVAL_DELTAS[self.time_horizon].total_seconds() * 1000)

        all_records: list[dict] = []
        current_start = start_ms

        while current_start < end_ms:
            response = client.get_kline(
                category="spot",
                symbol=api_symbol,
                interval=interval,
                start=current_start,
                end=end_ms,
                limit=1000,
            )

            result_list = response.get("result", {}).get("list", [])
            if not result_list:
                break

            # Bybit returns newest-first — reverse for chronological order
            result_list = list(reversed(result_list))

            for k in result_list:
                ts = datetime.utcfromtimestamp(int(k[0]) / 1000)
                all_records.append({
                    "date_time": ts,
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                })

            # Advance past the newest candle we received
            newest_ts = int(result_list[-1][0])
            current_start = newest_ts + delta_ms

            # Fewer than 1000 results means we've reached the end
            if len(result_list) < 1000:
                break

        if not all_records:
            return pd.DataFrame()

        df = pd.DataFrame(all_records)
        df.set_index("date_time", inplace=True)
        df = df[~df.index.duplicated(keep="first")]
        df.sort_index(inplace=True)
        return df

    # Missing-data handling

    def _fill_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill gaps in the OHLCV DataFrame using the configured strategy."""
        if df.empty:
            return df

        freq = PANDAS_FREQ.get(self.time_horizon)
        if freq is None:
            logger.warning("Cannot determine frequency for gap-filling; skipping.")
            return df

        # Build a complete date range and reindex
        full_range = pd.date_range(
            start=df.index.min(), end=df.index.max(), freq=freq,
        )
        df = df.reindex(full_range)
        df.index.name = "date_time"

        missing_count = int(df.isna().any(axis=1).sum())
        if missing_count == 0:
            return df

        if self.fill_strategy == "interpolation":
            df = df.interpolate(method="linear")
        elif self.fill_strategy == "forward_fill":
            df = df.ffill()
        elif self.fill_strategy == "drop":
            df = df.dropna()
        else:
            logger.warning(
                f"Unknown fill strategy '{self.fill_strategy}'; defaulting to interpolation."
            )
            df = df.interpolate(method="linear")

        logger.info(f"Filled {missing_count} missing row(s) using '{self.fill_strategy}'.")
        return df

    # Retry wrapper

    def _with_retry(self, func, *args, **kwargs):
        """Execute *func* with configurable retry logic."""
        last_exc = None
        for attempt in range(1, self.retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                last_exc = exc
                logger.warning(f"Attempt {attempt}/{self.retries} failed: {exc}")
                if attempt < self.retries:
                    time.sleep(self.retry_delay)

        raise RuntimeError(
            f"All {self.retries} attempt(s) failed. Last error: {last_exc}"
        ) from last_exc

    # Public API

    def download(self, symbol: str) -> None:
        """Download OHLCV data for a single symbol with incremental updates.

        1. Query the DB for the latest stored ``date_time``.
        2. Fetch only newer candles from the exchange API.
        3. Drop the last row (incomplete candle).
        4. Fill missing rows according to ``fill_missing_data`` config.
        5. Insert into the correct table.
        """
        table_name = self._table_name(symbol)

        # Determine effective start: resume from where we left off
        latest_dt = self._get_latest_datetime(table_name)

        if latest_dt is not None:
            delta = INTERVAL_DELTAS.get(self.time_horizon, timedelta(days=1))
            effective_start = latest_dt + delta
        else:
            effective_start = datetime.strptime(self.start_date, "%Y-%m-%d")

        end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")

        # Already up to date?
        if effective_start >= end_dt:
            logger.info(f"[{self.exchange}] {symbol}: already up to date.")
            return

        logger.info(
            f"[{self.exchange}] {symbol}: "
            f"fetching {effective_start.date()} → {end_dt.date()} ..."
        )

        # Fetch with retries
        if self.exchange == "binance":
            df = self._with_retry(self._fetch_binance, symbol, effective_start, end_dt)
        elif self.exchange == "bybit":
            df = self._with_retry(self._fetch_bybit, symbol, effective_start, end_dt)
        else:
            raise ValueError(f"Unsupported exchange: {self.exchange}")

        if df.empty:
            logger.info(f"[{self.exchange}] {symbol}: no new data returned.")
            return

        # Drop last row (incomplete candle)
        df = df.iloc[:-1]

        if df.empty:
            logger.info(f"[{self.exchange}] {symbol}: no complete candles.")
            return

        # Fill missing data
        df = self._fill_missing(df)

        # Insert into PostgreSQL
        rows = self._insert_rows(df, table_name)
        logger.info(f"[{self.exchange}] {symbol}: inserted {rows} rows.")

    def download_all(self, symbols: list[str]) -> None:
        """Download data for every symbol in the list."""
        logger.info(f"Starting {self.exchange.capitalize()} download plan for {len(symbols)} symbols.")
        for symbol in symbols:
            try:
                self.download(symbol)
                logger.info(f"Successfully finished processing {symbol} on {self.exchange.capitalize()}.")
            except Exception as exc:
                logger.error(f"Failed to process {symbol} on {self.exchange.capitalize()}: {exc}")
        logger.info(f"{self.exchange.capitalize()} download plan completed.")
