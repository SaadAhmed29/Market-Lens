"""
Fetches Reddit posts (with embedded top-N comments) for a set of crypto
symbols within a configurable date range, using the official Reddit API
via PRAW. Checks sentiment_data.raw_data first and only fetches the
portion of the date range not already stored, so reruns are cheap.
"""

import os
import logging
from datetime import datetime, timezone

import praw
import psycopg2
from psycopg2.extras import execute_values, Json

from dotenv import load_dotenv
load_dotenv()

# Config

SCHEMA_NAME = "sentiment_data"
TABLE_NAME = "raw_data"
TOP_N_COMMENTS = 10
LISTING_LIMIT = 1000  # Reddit's practical ceiling per listing/search query

# symbol -> list of subreddits to search
SYMBOL_SUBREDDITS = {
    "BTC": ["Bitcoin"],
    "ETH": ["ethereum"],
    "SOL": ["solana"],
    "MINA": ["mina"],
    "ADA": ["cardano"],
    "DOGE": ["dogecoin"],
    "SUI": ["sui"],
    "LTC": ["litecoin"],
}

# also search these general subreddits for keyword mentions of each symbol
GENERAL_SUBREDDITS = ["CryptoCurrency", "CryptoMarkets"]

# keyword used for general-subreddit search per symbol (full name works
# better than the raw ticker, since tickers like SOL/ADA are common words)
SYMBOL_KEYWORDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "MINA": "mina",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "SUI": "sui",
    "LTC": "litecoin",
}


def _parse_date(date_str, default=None):
    if not date_str:
        return default
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


FETCH_START_DATE = "2026-01-01"
FETCH_END_DATE = "2026-07-07"

START_DATE = _parse_date(FETCH_START_DATE)
END_DATE = _parse_date(FETCH_END_DATE, default=datetime.now(timezone.utc))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# Reddit client (PRAW)

def get_reddit_client():
    return praw.Reddit(
        client_id=os.getenv("client_id"),
        client_secret=os.getenv("client_secret"),
        user_agent=os.getenv("user_agent"),
    )


# Database

def get_connection():
    from utils.db import DB_CONFIG
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["name"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )


def get_existing_range(conn, symbol):
    """Return (min_date_time, max_date_time) already stored for this
    symbol, or (None, None) if nothing stored yet."""
    query = f"""
        SELECT MIN(date_time), MAX(date_time)
        FROM {SCHEMA_NAME}.{TABLE_NAME}
        WHERE symbol = %s
    """
    with conn.cursor() as cur:
        cur.execute(query, (symbol,))
        return cur.fetchone()


def get_missing_ranges(conn, symbol, start, end):
    """Compare the requested [start, end] window against what's already
    stored for this symbol, and return only the missing sub-range(s).

    NOTE: this assumes contiguous coverage (extending the stored range
    forward and/or backward). It will not detect isolated gaps *inside*
    an already-covered range — good enough for a rolling/incremental
    fetch pattern, but not a general-purpose gap filler.
    """
    existing_min, existing_max = get_existing_range(conn, symbol)

    if existing_min is None:
        return [(start, end)]

    missing = []
    if start < existing_min:
        missing.append((start, min(existing_min, end)))
    if end > existing_max:
        missing.append((max(existing_max, start), end))

    if not missing:
        log.info(
            "Symbol %s: requested range %s -> %s already covered by stored "
            "data (%s -> %s), skipping.",
            symbol, start.date(), end.date(), existing_min.date(), existing_max.date()
        )
    return missing


def save_items(conn, items: list, symbol: str):
    if not items:
        return

    rows = [
        (
            item["source_id"],
            symbol,
            item["subreddit"],
            item["title"],
            item["body"],
            item["score"],
            item["num_comments"],
            item["date_time"],
            Json(item["comments"]),
        )
        for item in items
    ]

    query = f"""
        INSERT INTO {SCHEMA_NAME}.{TABLE_NAME}
        (source_id, symbol, subreddit, title, body, score, num_comments,
         date_time, comments)
        VALUES %s
        ON CONFLICT (source_id) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, query, rows)
    conn.commit()


# Fetch helpers

def fetch_top_comments(submission, limit: int = TOP_N_COMMENTS) -> list:
    """Return up to `limit` top-level comments sorted by score, as a list
    of small dicts, ready to store as JSON."""
    try:
        submission.comment_sort = "top"
        submission.comments.replace_more(limit=0)
        top = []
        for comment in submission.comments[:limit]:
            top.append({
                "id": comment.id,
                "author": str(comment.author) if comment.author else None,
                "body": comment.body,
                "score": comment.score,
            })
        return top
    except Exception as e:
        log.warning("Failed to fetch comments for post %s: %s", submission.id, e)
        return []


def fetch_posts_in_range(reddit, subreddit_name: str, start_ts: float, end_ts: float, query: str = None) -> list:
    """Fetch posts from a subreddit within [start_ts, end_ts], newest first.

    See module docstring: limited to Reddit's ~1000-item listing ceiling,
    so this only reliably covers recent windows.
    """
    subreddit = reddit.subreddit(subreddit_name)
    listing = (
        subreddit.search(query, sort="new", limit=LISTING_LIMIT)
        if query else
        subreddit.new(limit=LISTING_LIMIT)
    )

    results = []
    for submission in listing:
        created = submission.created_utc
        if created > end_ts:
            continue  # newer than our window — keep scanning
        if created < start_ts:
            break  # sorted newest-first, so we're past our window now

        results.append({
            "source_id": submission.id,
            "subreddit": subreddit_name,
            "title": submission.title or "",
            "body": submission.selftext or "",
            "score": submission.score,
            "num_comments": submission.num_comments,
            "date_time": datetime.fromtimestamp(created, tz=timezone.utc),
            "comments": fetch_top_comments(submission),
        })

    return results


# Orchestration

def backfill_symbol(conn, reddit, symbol: str):
    subreddits = SYMBOL_SUBREDDITS.get(symbol, [])
    keyword = SYMBOL_KEYWORDS.get(symbol, symbol.lower())

    ranges = get_missing_ranges(conn, symbol, START_DATE, END_DATE)
    if not ranges:
        return

    for start, end in ranges:
        log.info("Fetching %s for missing range %s -> %s", symbol, start.date(), end.date())
        start_ts, end_ts = start.timestamp(), end.timestamp()

        for sub in subreddits:
            posts = fetch_posts_in_range(reddit, sub, start_ts, end_ts, query=None)
            save_items(conn, posts, symbol)
            log.info("  r/%s: +%d posts", sub, len(posts))

        for sub in GENERAL_SUBREDDITS:
            posts = fetch_posts_in_range(reddit, sub, start_ts, end_ts, query=keyword)
            save_items(conn, posts, symbol)
            log.info("  r/%s (keyword='%s'): +%d posts", sub, keyword, len(posts))


def main():
    reddit = get_reddit_client()
    conn = get_connection()
    try:
        for symbol in SYMBOL_SUBREDDITS:
            backfill_symbol(conn, reddit, symbol)
    finally:
        conn.close()
    log.info("Fetch complete. Data stored in %s.%s", SCHEMA_NAME, TABLE_NAME)


if __name__ == "__main__":
    main()