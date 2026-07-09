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

from sentiment_analysis.db import get_connection, get_missing_ranges, save_raw_items, create_sentiment_config_table, load_sentiment_config

# Config

SCHEMA_NAME = "sentiment_data"
TABLE_NAME = "raw_data"

create_sentiment_config_table()
sentiment_config = load_sentiment_config()

TOP_N_COMMENTS = sentiment_config.get("top_n_comments", 10)
LISTING_LIMIT = sentiment_config.get("listing_limit", 10)
SYMBOL_SUBREDDITS = sentiment_config.get("symbol_subreddits", {})
GENERAL_SUBREDDITS = sentiment_config.get("general_subreddits", [])
SYMBOL_KEYWORDS = sentiment_config.get("symbol_keywords", {})


def _parse_date(date_str, default=None):
    if not date_str:
        return default
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


FETCH_START_DATE = "2026-07-08"
FETCH_END_DATE = "2026-07-09"

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


# Fetch helpers

def fetch_top_comments(submission, limit: int = TOP_N_COMMENTS) -> list:
    """Return up to `limit` top-level comments sorted by score, as a list
    of small dicts, ready to store as JSON."""
    try:
        submission.comment_sort = "top"
        submission.comments.replace_more(limit=0)
        top = []
        for comment in submission.comments[:limit]:
            top.append(comment.body)
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

    ranges = get_missing_ranges(conn, SCHEMA_NAME, TABLE_NAME, START_DATE, END_DATE, symbol)
    if not ranges:
        return

    for start, end in ranges:
        log.info("Fetching %s for missing range %s -> %s", symbol, start.date(), end.date())
        start_ts, end_ts = start.timestamp(), end.timestamp()

        for sub in subreddits:
            posts = fetch_posts_in_range(reddit, sub, start_ts, end_ts, query=None)
            save_raw_items(conn, posts, symbol, SCHEMA_NAME, TABLE_NAME)
            log.info("  r/%s: +%d posts", sub, len(posts))

        for sub in GENERAL_SUBREDDITS:
            posts = fetch_posts_in_range(reddit, sub, start_ts, end_ts, query=keyword)
            save_raw_items(conn, posts, symbol, SCHEMA_NAME, TABLE_NAME)
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