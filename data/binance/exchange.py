"""
MarketLens - Binance Exchange API
Fetches OHLCV candle data from the Binance API.
"""

from datetime import datetime, timezone

import pandas as pd


def fetch_binance(client, symbol: str, interval: str,
                  start_dt: datetime, end_dt: datetime) -> pd.DataFrame:

    """Fetch OHLCV candles from Binance via ``get_historical_klines``."""

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
            "date_time": datetime.utcfromtimestamp(k[0] / 1000).replace(tzinfo=timezone.utc),
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
