"""
MarketLens — Sentiment Module
Aggregates all data required by the /api/sentiment endpoint.
Queries the sentiment_data.cleaned_data table for post samples,
distribution counts, per-symbol sentiment, and overall market sentiment.
"""

import sys
from pathlib import Path
from collections import defaultdict

from sqlalchemy import text

# Path setup: allow imports from project root regardless of how this module
# is imported (e.g. when FastAPI is launched from backend/).
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.db import get_engine  # noqa: E402

# Label mapping used throughout the module
_LABEL_MAP = {"positive": "bullish", "negative": "bearish", "neutral": "neutral"}


# Individual data-fetching helpers


def _fetch_sample_posts(conn) -> dict[str, list[dict]]:
    """
    For each symbol fetch the top 3 posts per label (positive, negative,
    neutral), ranked by confidence_score DESC.  Only rows with non-null /
    non-empty title, body, label, confidence_score and a non-empty comments
    array are considered.

    Returns a dict keyed by symbol, each containing a list of post dicts.
    """
    query = text("""
        WITH ranked AS (
            SELECT
                symbol,
                title,
                body,
                comments,
                label,
                ROUND(confidence_score::numeric, 2) AS confidence_score,
                ROW_NUMBER() OVER (
                    PARTITION BY symbol, label
                    ORDER BY confidence_score DESC
                ) AS rn
            FROM sentiment_data.cleaned_data
            WHERE title       IS NOT NULL AND title       <> ''
              AND body        IS NOT NULL AND body        <> ''
              AND label       IS NOT NULL AND label       <> ''
              AND confidence_score IS NOT NULL
              AND comments    IS NOT NULL AND array_length(comments, 1) > 0
        )
        SELECT symbol, title, body, comments, label, confidence_score
        FROM ranked
        WHERE rn <= 3
        ORDER BY symbol, label, confidence_score DESC
    """)

    try:
        rows = conn.execute(query).mappings().fetchall()
    except Exception:
        return {}

    result: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        result[row["symbol"]].append({
            "symbol": row["symbol"],
            "title": row["title"],
            "body": row["body"],
            "comments": list(row["comments"]) if row["comments"] else [],
            "label": _LABEL_MAP.get(row["label"], row["label"]),
            "confidence_score": float(row["confidence_score"]),
        })

    return dict(result)


def _fetch_overall_distribution(conn) -> dict[str, int]:
    """
    Count total rows grouped by label across the entire table.

    Returns {"bullish": count, "bearish": count, "neutral": count}.
    """
    query = text("""
        SELECT label, COUNT(*) AS cnt
        FROM sentiment_data.cleaned_data
        GROUP BY label
    """)

    distribution = {"bullish": 0, "bearish": 0, "neutral": 0}

    try:
        rows = conn.execute(query).mappings().fetchall()
    except Exception:
        return distribution

    for row in rows:
        mapped = _LABEL_MAP.get(row["label"], row["label"])
        distribution[mapped] = int(row["cnt"])

    return distribution


def _fetch_per_symbol_distribution(conn) -> dict[str, dict[str, int]]:
    """
    Count rows grouped by symbol and label.

    Returns e.g. {"DOGE": {"bullish": 10, "bearish": 5, "neutral": 3}, …}
    """
    query = text("""
        SELECT symbol, label, COUNT(*) AS cnt
        FROM sentiment_data.cleaned_data
        GROUP BY symbol, label
        ORDER BY symbol, label
    """)

    try:
        rows = conn.execute(query).mappings().fetchall()
    except Exception:
        return {}

    result: dict[str, dict[str, int]] = defaultdict(
        lambda: {"bullish": 0, "bearish": 0, "neutral": 0}
    )
    for row in rows:
        mapped = _LABEL_MAP.get(row["label"], row["label"])
        result[row["symbol"]][mapped] = int(row["cnt"])

    return dict(result)


def _fetch_symbol_sentiment(conn) -> dict[str, str]:
    """
    For each symbol find the mode (most frequent label).

    Returns e.g. {"DOGE": "bullish", "BTC": "bearish", …}.
    """
    query = text("""
        SELECT DISTINCT ON (symbol) symbol, label
        FROM (
            SELECT symbol, label, COUNT(*) AS cnt
            FROM sentiment_data.cleaned_data
            GROUP BY symbol, label
        ) sub
        ORDER BY symbol, cnt DESC
    """)

    try:
        rows = conn.execute(query).mappings().fetchall()
    except Exception:
        return {}

    return {row["symbol"]: _LABEL_MAP.get(row["label"], row["label"]) for row in rows}


def _fetch_market_sentiment(conn) -> str:
    """
    Find the mode of label across the entire table.

    Returns a single string: "bullish", "bearish", or "neutral".
    """
    query = text("""
        SELECT label
        FROM sentiment_data.cleaned_data
        GROUP BY label
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    try:
        row = conn.execute(query).mappings().fetchone()
    except Exception:
        return "neutral"

    if row is None:
        return "neutral"

    return _LABEL_MAP.get(row["label"], row["label"])


# Main entry point


def get_sentiment_data() -> dict:
    """
    Aggregate all sentiment data and return a single dict.
    Uses the shared SQLAlchemy engine from utils/db.py for all DB queries.
    Falls back to sensible defaults (empty dicts / "neutral") on any failure.
    """
    engine = get_engine()

    with engine.connect() as conn:
        sample_posts = _fetch_sample_posts(conn)
        overall_distribution = _fetch_overall_distribution(conn)
        per_symbol_distribution = _fetch_per_symbol_distribution(conn)
        symbol_sentiment = _fetch_symbol_sentiment(conn)
        market_sentiment = _fetch_market_sentiment(conn)

    return {
        "sample_posts": sample_posts,
        "overall_distribution": overall_distribution,
        "per_symbol_distribution": per_symbol_distribution,
        "symbol_sentiment": symbol_sentiment,
        "market_sentiment": market_sentiment,
    }
