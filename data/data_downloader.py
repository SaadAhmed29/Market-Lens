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
from utils.intervals import BYBIT_INTERVALS, PANDAS_FREQ, INTERVAL_DELTAS

logger = logging.getLogger(__name__)


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

        self.engine = get_engine()
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
        """Return the DB table name for a given symbol, e.g. ``binance_data.binance_btc``."""
        return f"{self.exchange}_data.{self.exchange}_{symbol.lower()}"

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
        interval = self.time_horizon

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


def get_resampled_df(df: pd.DataFrame, time_frame: str, resample_1m: bool = False):
    """
    Takes a raw OHLCV dataframe and resamples it to the given time_frame.
    If resample_1m=True, also returns a 1-minute resampled version.
    """
    if df is None or df.empty:
        return df, (df if resample_1m else None)
        
    agg_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    
    res_freq = PANDAS_FREQ.get(time_frame, time_frame)
    resampled_df = df.resample(res_freq).agg(agg_dict).dropna()
    
    df_1m = None
    if resample_1m:
        freq_1m = PANDAS_FREQ.get("1m", "1min")
        df_1m = df.resample(freq_1m).agg(agg_dict).dropna()
        
    return resampled_df, df_1m


def get_updated_df(exchange: str, symbol: str, start, end, time_frame: str, resample_1m: bool = False):
    """
    Checks the database for data within the given time range.
    Fetches missing data from API if necessary and combines it with DB data.
    Does not update the database.
    """
    start_dt = pd.to_datetime(start)
    end_dt = pd.to_datetime(end)
    
    engine = get_engine()
    table_name = f"{exchange}_data.{exchange}_{symbol.lower()}"
    
    query = text(f"""
        SELECT * FROM {table_name} 
        WHERE date_time >= :start AND date_time <= :end
        ORDER BY date_time ASC
    """)
    
    try:
        with engine.connect() as conn:
            db_df = pd.read_sql(query, conn, params={"start": start_dt, "end": end_dt}, index_col="date_time")
    except Exception as e:
        logger.warning(f"Failed to read from DB: {e}")
        db_df = pd.DataFrame()
        
    missing_ranges = []
    if db_df.empty:
        missing_ranges.append((start_dt, end_dt))
    else:
        db_start = db_df.index.min()
        db_end = db_df.index.max()
        from datetime import timedelta
        delta = timedelta(minutes=1)
        if db_start > start_dt:
            missing_ranges.append((start_dt, db_start - delta))
        if db_end < end_dt:
            missing_ranges.append((db_end + delta, end_dt))
            
    api_dfs = []
    if missing_ranges:
        fetcher_config = {
            "exchange": exchange,
            "time_horizon": "1m",
            "start_date": start_dt.strftime("%Y-%m-%d"),
            "end_date": end_dt.strftime("%Y-%m-%d"),
            "fill_missing_data": "interpolation",
            "retries": 3,
            "retry_delay": 5
        }
        fetcher = DataFetcher(fetcher_config)
        
        for m_start, m_end in missing_ranges:
            if m_start >= m_end:
                continue
            if exchange == "binance":
                df_part = fetcher._with_retry(fetcher._fetch_binance, symbol, m_start, m_end)
            elif exchange == "bybit":
                df_part = fetcher._with_retry(fetcher._fetch_bybit, symbol, m_start, m_end)
            else:
                continue
                
            if not df_part.empty:
                api_dfs.append(df_part)
                
    if api_dfs:
        api_df = pd.concat(api_dfs)
        final_df = pd.concat([db_df, api_df])
    else:
        final_df = db_df
        
    if not final_df.empty:
        final_df = final_df[~final_df.index.duplicated(keep="last")]
        final_df.sort_index(inplace=True)
        final_df = final_df[(final_df.index >= start_dt) & (final_df.index <= end_dt)]
        
    return get_resampled_df(final_df, time_frame, resample_1m)
