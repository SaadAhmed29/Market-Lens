"""
MarketLens - Interval Mappings
Defines time horizon mappings for different exchange APIs and pandas frequencies.
"""

from datetime import timedelta

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
