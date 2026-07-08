"""
Reads raw Reddit posts from sentiment_data.raw_data, cleans the text,
deduplicates, and saves results into sentiment_data.cleaned_data.
"""

import re
import logging
import json

import emoji
import pandas as pd
from bs4 import BeautifulSoup
from utils.db import get_engine
from langdetect import detect, LangDetectException

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


def _clean_comments(comments_val):
    """Parse comments, clean each body, filter empty or non-English, and repack."""
    if comments_val is None:
        return comments_val
    if isinstance(comments_val, float) and pd.isna(comments_val):
        return comments_val
    if isinstance(comments_val, (list, str, dict)) and not comments_val:
        return comments_val
        
    is_str = isinstance(comments_val, str)
    if is_str:
        try:
            comments_list = json.loads(comments_val)
        except json.JSONDecodeError:
            return comments_val
    elif isinstance(comments_val, list):
        comments_list = comments_val
    else:
        return comments_val
        
    cleaned_comments = []
    for comment in comments_list:
        if not isinstance(comment, dict) or 'body' not in comment:
            continue
            
        cleaned_body = _clean_text(comment['body'])
        if not cleaned_body:
            continue
            
        try:
            if detect(cleaned_body) == 'en':
                # Important: create a new dictionary to avoid modifying the original if passed by reference
                cleaned_comment = comment.copy()
                cleaned_comment['body'] = cleaned_body
                cleaned_comments.append(cleaned_comment)
        except LangDetectException:
            continue
            
    if is_str:
        return json.dumps(cleaned_comments)
    return json.dumps(cleaned_comments) if is_str else cleaned_comments


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

    # Clean title and body
    df["title"] = df["title"].fillna("").apply(_clean_text)
    df["body"] = df["body"].fillna("").apply(_clean_text)

    # Clean comments if the column exists
    if "comments" in df.columns:
        df["comments"] = df["comments"].apply(_clean_comments)

    # Empty Row Check: drop rows where both title and body are empty
    before_post = len(df)
    df = df[(df["title"] != "") | (df["body"] != "")]
    log.info("Dropped %d rows with both empty title and body after cleaning", before_post - len(df))

    # Language Detection: drop row if either title or body is non-English
    def is_valid_language(row):
        title = row["title"]
        body = row["body"]
        
        if title:
            try:
                if detect(title) != 'en':
                    return False
            except LangDetectException:
                return False
                
        if body:
            try:
                if detect(body) != 'en':
                    return False
            except LangDetectException:
                return False
                
        return True

    before_lang = len(df)
    df = df[df.apply(is_valid_language, axis=1)]
    log.info("Dropped %d rows due to non-English title or body", before_lang - len(df))

    # Deduplicate on cleaned title + body
    before_dedup = len(df)
    df = df.drop_duplicates(subset=["title", "body"])
    log.info("Removed %d duplicate rows", before_dedup - len(df))

    # Sort by pk
    if "pk" in df.columns:
        df = df.sort_values(by="pk")

    # Schema Update: add label and confidence_score
    if "label" not in df.columns:
        df["label"] = None
    if "confidence_score" not in df.columns:
        df["confidence_score"] = None

    return df.reset_index(drop=True)


def save_cleaned(engine, df: pd.DataFrame) -> None:
    """Write cleaned rows into the cleaned_data table."""
    # Drop the pk column so the DB generates new serial ids
    cols = [c for c in df.columns if c != "pk"]
    
    # If comments was left as a list/dict, converting it to JSON string might be necessary for to_sql depending on DB adapter
    if "comments" in df.columns:
        df["comments"] = df["comments"].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
        
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
