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
from langdetect import detect, LangDetectException
from sentiment_analysis.db import load_raw_data, save_cleaned_data

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
    """Clean each comment string, filter empty or non-English, and repack."""
    if comments_val is None:
        return comments_val
    if isinstance(comments_val, float) and pd.isna(comments_val):
        return comments_val
    if isinstance(comments_val, (list, str, dict)) and not comments_val:
        return comments_val
        
    if hasattr(comments_val, 'tolist'):
        comments_list = comments_val.tolist()
    elif isinstance(comments_val, list):
        comments_list = comments_val
    else:
        return comments_val
        
    cleaned_comments = []
    for comment in comments_list:
        if not isinstance(comment, str):
            continue
            
        cleaned_body = _clean_text(comment)
        if not cleaned_body:
            continue
            
        try:
            if detect(cleaned_body) == 'en':
                cleaned_comments.append(cleaned_body)
        except LangDetectException:
            continue
            
    return cleaned_comments


# Pipeline

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


# Entry point

def run_prep(engine, start_date=None, end_date=None):
    df = load_raw_data(engine, SCHEMA, RAW_TABLE, start_date, end_date)
    if df.empty:
        log.info("No data in raw_data — nothing to clean.")
        return

    df = clean(df)
    save_cleaned_data(engine, df, SCHEMA, CLEAN_TABLE)
    log.info("Data prep complete.")

def main():
    engine = get_engine()
    run_prep(engine)

if __name__ == "__main__":
    main()
