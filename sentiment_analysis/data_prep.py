"""
Reads raw Reddit posts from sentiment_data.raw_data, cleans the text,
deduplicates, and saves results into sentiment_data.cleaned_data.
"""

import re
import logging

import emoji
import pandas as pd
from bs4 import BeautifulSoup
from utils.db import get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

SCHEMA = "sentiment_data"
RAW_TABLE = "raw_data"
CLEAN_TABLE = "cleaned_data"


# Cleaning helpers

def _clean_text(text: str) -> str:
    """Apply all cleaning steps to a single string."""
    if not text:
        return ""

    # Emojis → text representation (before lowercasing so labels stay readable)
    text = emoji.demojize(text, delimiters=(" ", " "))

    # Lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)

    # Remove HTML tags
    text = BeautifulSoup(text, "html.parser").get_text()

    # Remove punctuation (keep letters, digits, whitespace)
    text = re.sub(r"[^\w\s]", "", text)

    # Collapse extra whitespace and strip
    text = re.sub(r"\s+", " ", text).strip()

    return text


# Pipeline

def load_raw(engine) -> pd.DataFrame:
    """Read all rows from raw_data."""
    query = f"SELECT * FROM {SCHEMA}.{RAW_TABLE}"
    df = pd.read_sql(query, engine)
    log.info("Loaded %d rows from %s.%s", len(df), SCHEMA, RAW_TABLE)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop empty bodies, clean text columns, and deduplicate."""
    initial = len(df)

    # Drop rows where body is null or empty string
    df = df[df["body"].notna() & (df["body"].str.strip() != "")]
    log.info("Dropped %d rows with null/empty body", initial - len(df))

    # Clean title and body
    df["title"] = df["title"].fillna("").apply(_clean_text)
    df["body"] = df["body"].apply(_clean_text)

    # Drop rows where body became empty after cleaning
    before_post = len(df)
    df = df[df["body"].str.strip() != ""]
    log.info("Dropped %d rows with empty body after cleaning", before_post - len(df))

    # Deduplicate on cleaned title + body
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["title", "body"])
    log.info("Removed %d duplicate rows", before_dedup - len(df))

    return df.reset_index(drop=True)


def save_cleaned(engine, df: pd.DataFrame) -> None:
    """Write cleaned rows into the cleaned_data table."""
    # Drop the pk column so the DB generates new serial ids
    cols = [c for c in df.columns if c != "pk"]
    df[cols].to_sql(
        CLEAN_TABLE,
        engine,
        schema=SCHEMA,
        if_exists="append",
        index=False,
    )
    log.info("Saved %d rows to %s.%s", len(df), SCHEMA, CLEAN_TABLE)


# Entry point

def main():
    engine = get_engine()

    df = load_raw(engine)
    if df.empty:
        log.info("No data in raw_data — nothing to clean.")
        return

    df = clean(df)
    save_cleaned(engine, df)
    log.info("Data prep complete.")


if __name__ == "__main__":
    main()
