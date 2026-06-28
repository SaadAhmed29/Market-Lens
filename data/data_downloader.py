"""
MarketLens - Data Downloader
Fetches OHLCV candle data from Binance and Bybit APIs.
Supports incremental updates, retry logic, and missing-data interpolation.
"""

import time
import logging
from datetime import datetime, timedelta, timezone

import pandas as pd
from sqlalchemy import text

from data.binance.exchange import fetch_binance
from data.bybit.exchange import fetch_bybit
from utils.db import get_engine, table_name, get_latest_datetime, insert_rows
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

    # Exchange fetch dispatchers

    def _fetch_binance(self, symbol: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
        """Fetch OHLCV candles from Binance via ``get_historical_klines``."""
        return fetch_binance(self._get_client(), symbol, self.time_horizon, start_dt, end_dt)

    def _fetch_bybit(self, symbol: str, start_dt: datetime, end_dt: datetime) -> pd.DataFrame:
        """Fetch OHLCV candles from Bybit via ``get_kline``, with pagination."""
        interval = BYBIT_INTERVALS.get(self.time_horizon)
        if interval is None:
            raise ValueError(f"Unsupported time_horizon for Bybit: {self.time_horizon}")
        delta = INTERVAL_DELTAS[self.time_horizon]
        return fetch_bybit(self._get_client(), symbol, interval, start_dt, end_dt, delta)

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
        tbl_name = table_name(self.exchange, symbol)

        # Determine effective start: resume from where we left off
        latest_dt = get_latest_datetime(self.engine, tbl_name)

        if latest_dt is not None:
            if latest_dt.tzinfo is None:
                latest_dt = latest_dt.replace(tzinfo=timezone.utc)
            effective_start = latest_dt
            is_incremental = True
        else:
            effective_start = pd.to_datetime(self.start_date, utc=True).to_pydatetime()
            is_incremental = False

        end_dt = pd.to_datetime(self.end_date, utc=True).to_pydatetime()

        # Already up to date?
        if effective_start >= end_dt:
            logger.info(f"[{self.exchange}] {symbol}: already up to date.")
            return

        logger.info(
            f"[{self.exchange}] {symbol}: "
            f"fetching {effective_start.date()} -> {end_dt.date()} ..."
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

        # Compute volume percentage change
        df['volume'] = df['volume'].pct_change()
        
        if is_incremental:
            # Drop the overlapping candle we used just for pct_change reference
            df = df.iloc[1:]
        else:
            # First fetch ever, set first pct_change to 0
            df.loc[df.index[0], 'volume'] = 0.0

        if df.empty:
            logger.info(f"[{self.exchange}] {symbol}: no new data after processing volume.")
            return
            
        # Fill missing data
        df = self._fill_missing(df)
        
        # Round everything to 4 decimal places
        df = df.round(4)

        # Insert into PostgreSQL
        rows = insert_rows(self.engine, df, tbl_name)
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

    # DataFrame helpers

    @staticmethod
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
            'volume': 'mean'
        }
        
        res_freq = PANDAS_FREQ.get(time_frame, time_frame)
        resampled_df = df.resample(res_freq).agg(agg_dict).dropna().round(4)
        
        df_1m = None
        if resample_1m:
            freq_1m = PANDAS_FREQ.get("1m", "1min")
            df_1m = df.resample(freq_1m).agg(agg_dict).dropna().round(4)
            
        return resampled_df, df_1m

    @staticmethod
    def get_updated_df(exchange: str, symbol: str, start, end,
                       time_frame: str, resample_1m: bool = False):
        """
        Checks the database for data within the given time range.
        Fetches missing data from API if necessary and combines it with DB data.
        Does not update the database.
        """
        start_dt = pd.to_datetime(start, utc=True)
        end_dt = pd.to_datetime(end, utc=True)
        
        engine = get_engine()
        tbl_name = table_name(exchange, symbol)
        
        query = text(f"""
            SELECT * FROM {tbl_name} 
            WHERE date_time >= :start AND date_time <= :end
            ORDER BY date_time ASC
        """)
        
        try:
            with engine.connect() as conn:
                db_df = pd.read_sql(query, conn, params={"start": start_dt, "end": end_dt}, index_col="date_time")
                if not db_df.empty:
                    db_df.index = pd.to_datetime(db_df.index, utc=True)
        except Exception as e:
            logger.warning(f"Failed to read from DB: {e}")
            db_df = pd.DataFrame()
            
        missing_ranges = []
        if db_df.empty:
            delta = timedelta(minutes=1)
            missing_ranges.append((start_dt - delta, end_dt))
        else:
            db_start = db_df.index.min()
            db_end = db_df.index.max()
            delta = timedelta(minutes=1)
            if db_start > start_dt:
                missing_ranges.append((start_dt - delta, db_start - delta))
            if db_end < end_dt:
                missing_ranges.append((db_end, end_dt))
                
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
                    df_part['volume'] = df_part['volume'].pct_change().fillna(0.0)
                    df_part = df_part[df_part.index > m_start]
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
            final_df = final_df.round(4)
            
        return DataFetcher.get_resampled_df(final_df, time_frame, resample_1m)
