"""
Fetches historical Reddit posts + comments for a set of crypto
symbols using PullPush.io (primary) and Arctic Shift (fallback), storing
results in the `sentiment_data.raw_data` table of an existing Postgres
database.
"""

import os
import time
import logging
from datetime import datetime, timedelta, timezone

import requests
import psycopg2
from psycopg2.extras import execute_values

# Config

SCHEMA_NAME = "sentiment_data"
TABLE_NAME = "raw_data"

DAYS_BACK = 90          # how far back to backfill
CHUNK_DAYS = 5           # window size per request batch (avoids timeouts)
PAGE_SIZE = 100          # PullPush max results per call
REQUEST_DELAY_SEC = 1.0  # be polite to the free API
MAX_RETRIES = 3
RETRY_BACKOFF_SEC = 5

PULLPUSH_BASE = "https://api.pullpush.io/reddit/search"
ARCTIC_SHIFT_BASE = "https://arctic-shift.photon-reddit.com/api"

# symbol -> list of subreddits to search
SYMBOL_SUBREDDITS = {
    "BTC": ["Bitcoin"],
}

# also search these general subreddits for keyword mentions of each symbol
GENERAL_SUBREDDITS = ["CryptoCurrency", "CryptoMarkets"]

# keyword used for general-subreddit search per symbol (full name works better
# than the raw ticker, since tickers like SOL/ADA are common English words)
SYMBOL_KEYWORDS = {
    "BTC": "bitcoin", 
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


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



def save_items(conn, items: list, symbol: str):
    if not items:
        return

    rows = [
        (
            symbol,
            item.get("subreddit"),
            item.get("title", ""),
            item.get("selftext") or item.get("body") or "",
            item.get("score", 0),
            item.get("num_comments", 0),
        )
        for item in items
    ]

    query = f"""
        INSERT INTO {SCHEMA_NAME}.{TABLE_NAME}
        (symbol, subreddit, title, body, score, num_comments)
        VALUES %s
    """

    with conn.cursor() as cur:
        execute_values(cur, query, rows)
    conn.commit()


# PullPush client (primary)

def _request_with_retries(url: str, params: dict) -> dict | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            log.warning(
                "Non-200 response (%s) on attempt %d/%d: %s",
                resp.status_code, attempt, MAX_RETRIES, resp.text[:200]
            )
        except requests.RequestException as e:
            log.warning("Request failed (attempt %d/%d): %s", attempt, MAX_RETRIES, e)
        time.sleep(RETRY_BACKOFF_SEC * attempt)
    return None


def pullpush_search(
    mode: str,           # "submission" or "comment"
    subreddit: str = None,
    query: str = None,
    after_ts: int = None,
    before_ts: int = None,
    size: int = PAGE_SIZE,
) -> list:
    url = f"{PULLPUSH_BASE}/{mode}/"
    params = {"size": size, "sort": "asc", "sort_type": "created_utc"}
    if subreddit:
        params["subreddit"] = subreddit
    if query:
        params["q"] = query
    if after_ts:
        params["after"] = after_ts
    if before_ts:
        params["before"] = before_ts

    data = _request_with_retries(url, params)
    if data is None:
        return []
    return data.get("data", [])


# Arctic Shift client (fallback — subreddit-scoped only, no cross-sub q param)

def arctic_shift_search(
    mode: str,           # "posts" or "comments"
    subreddit: str,
    after_ts: int,
    before_ts: int,
    query: str = None,
    limit="auto",        # 1-100, or "auto" (100-1000 depending on server load)
) -> list:
    url = f"{ARCTIC_SHIFT_BASE}/{mode}/search"
    params = {
        "subreddit": subreddit,
        "after": after_ts,     # Arctic Shift accepts epoch seconds directly
        "before": before_ts,
        "sort": "asc",
        "limit": limit,
    }
    if query:
        # posts use `query` (searches title+selftext), comments use `body`
        params["query" if mode == "posts" else "body"] = query

    data = _request_with_retries(url, params)
    if data is None:
        return []
    return data.get("data", [])


def arctic_shift_search_paginated(
    mode: str,           # "posts" or "comments"
    subreddit: str,
    start_ts: int,
    end_ts: int,
    query: str = None,
) -> list:
    """Paginate Arctic Shift the same way as PullPush: advance `after`
    using the last item's created_utc until the window is exhausted."""
    all_items = []
    cursor = start_ts
    while cursor < end_ts:
        batch = arctic_shift_search(mode, subreddit, cursor, end_ts, query=query)
        if not batch:
            break
        all_items.extend(batch)
        last_created = batch[-1].get("created_utc", cursor)
        if last_created <= cursor:
            break  # safety: avoid infinite loop if the API doesn't advance
        cursor = last_created + 1
        time.sleep(REQUEST_DELAY_SEC)
    return all_items


# Fetch orchestration

def fetch_window(
    symbol: str,
    subreddit: str,
    start_ts: int,
    end_ts: int,
    query: str = None,
) -> tuple:
    """Fetch submissions + comments for one subreddit/time-window,
    paginating until exhausted. Falls back to Arctic Shift if PullPush
    returns nothing (e.g. during an outage)."""

    all_submissions = []
    all_comments = []

    # ---- submissions, paginated ----
    cursor = start_ts
    while cursor < end_ts:
        batch = pullpush_search(
            mode="submission",
            subreddit=subreddit,
            query=query,
            after_ts=cursor,
            before_ts=end_ts,
        )
        if not batch:
            break
        all_submissions.extend(batch)
        last_created = batch[-1].get("created_utc", cursor)
        if last_created <= cursor:
            break  # safety: avoid infinite loop if API doesn't advance
        cursor = last_created + 1
        time.sleep(REQUEST_DELAY_SEC)
        if len(batch) < PAGE_SIZE:
            break  # last page

    # ---- comments, paginated ----
    cursor = start_ts
    while cursor < end_ts:
        batch = pullpush_search(
            mode="comment",
            subreddit=subreddit,
            query=query,
            after_ts=cursor,
            before_ts=end_ts,
        )
        if not batch:
            break
        all_comments.extend(batch)
        last_created = batch[-1].get("created_utc", cursor)
        if last_created <= cursor:
            break
        cursor = last_created + 1
        time.sleep(REQUEST_DELAY_SEC)
        if len(batch) < PAGE_SIZE:
            break

    # ---- fallback to Arctic Shift if PullPush gave us nothing at all ----
    if not all_submissions and not all_comments:
        log.info(
            "PullPush returned nothing for r/%s (%s), trying Arctic Shift fallback",
            subreddit, symbol
        )
        all_submissions = arctic_shift_search_paginated(
            "posts", subreddit, start_ts, end_ts, query=query
        )
        all_comments = arctic_shift_search_paginated(
            "comments", subreddit, start_ts, end_ts, query=query
        )

    return all_submissions, all_comments


def backfill_symbol(conn, symbol: str, days_back: int = DAYS_BACK):
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)

    subreddits = SYMBOL_SUBREDDITS.get(symbol, [])
    keyword = SYMBOL_KEYWORDS.get(symbol, symbol.lower())

    # 1) dedicated subreddits — no keyword filter needed, whole sub is on-topic
    for sub in subreddits:
        log.info("Backfilling r/%s for %s ...", sub, symbol)
        _backfill_subreddit_chunked(conn, symbol, sub, start, end, query=None)

    # 2) general subreddits — filter by keyword since they cover many coins
    for sub in GENERAL_SUBREDDITS:
        log.info("Backfilling r/%s for %s (keyword='%s') ...", sub, symbol, keyword)
        _backfill_subreddit_chunked(conn, symbol, sub, start, end, query=keyword)


def _backfill_subreddit_chunked(
    conn,
    symbol: str,
    subreddit: str,
    start: datetime,
    end: datetime,
    query: str = None,
):
    current = start
    total_posts, total_comments = 0, 0

    while current < end:
        chunk_end = min(current + timedelta(days=CHUNK_DAYS), end)
        start_ts = int(current.timestamp())
        end_ts = int(chunk_end.timestamp())

        submissions, comments = fetch_window(symbol, subreddit, start_ts, end_ts, query)

        if submissions:
            save_items(conn, submissions, symbol)
            total_posts += len(submissions)
        if comments:
            save_items(conn, comments, symbol)
            total_comments += len(comments)

        log.info(
            "  %s: %s -> %s | +%d posts, +%d comments",
            subreddit, current.date(), chunk_end.date(), len(submissions), len(comments)
        )

        current = chunk_end

    log.info(
        "Done r/%s for %s: %d posts, %d comments total",
        subreddit, symbol, total_posts, total_comments
    )


# Entry point

def main():
    conn = get_connection()
    try:
        for symbol in SYMBOL_SUBREDDITS:
            backfill_symbol(conn, symbol)
    finally:
        conn.close()
    log.info(
        "Backfill complete. Data stored in %s.%s",
        SCHEMA_NAME, TABLE_NAME
    )


if __name__ == "__main__":
    main()