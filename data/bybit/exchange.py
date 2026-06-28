"""
MarketLens - Bybit Exchange API
Fetches OHLCV candle data from the Bybit API with pagination.
"""

from datetime import datetime, timedelta, timezone

import pandas as pd


def fetch_bybit(client, symbol: str, interval: str,
                start_dt: datetime, end_dt: datetime,
                delta: timedelta) -> pd.DataFrame:

    """Fetch OHLCV candles from Bybit via ``get_kline``, with pagination."""

    api_symbol = f"{symbol}USDT"
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    delta_ms = int(delta.total_seconds() * 1000)

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
            ts = datetime.utcfromtimestamp(int(k[0]) / 1000).replace(tzinfo=timezone.utc)
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
