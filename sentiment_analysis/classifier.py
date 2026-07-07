"""
Reads cleaned posts from sentiment_data.cleaned_data, classifies them using FinBERT,
and writes the results (label and confidence_score) back to the same table.
"""

import logging
import pandas as pd
from sqlalchemy import text
from transformers import pipeline
from utils.db import get_engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

SCHEMA = "sentiment_data"
TABLE = "cleaned_data"
BATCH_SIZE = 128


def ensure_columns(engine):
    """Add label and confidence_score columns to cleaned_data if they don't exist."""
    with engine.begin() as conn:
        conn.execute(text(f"""
            ALTER TABLE {SCHEMA}.{TABLE}
            ADD COLUMN IF NOT EXISTS label VARCHAR,
            ADD COLUMN IF NOT EXISTS confidence_score FLOAT;
        """))
    log.info("Ensured label and confidence_score columns exist in %s.%s.", SCHEMA, TABLE)


def load_data(engine) -> pd.DataFrame:
    """Read first 5k rows from cleaned_data."""
    query = f"SELECT pk, title, body FROM {SCHEMA}.{TABLE} ORDER BY pk LIMIT 5000"
    df = pd.read_sql(query, engine)
    log.info("Loaded %d rows from %s.%s", len(df), SCHEMA, TABLE)
    return df


def classify(df: pd.DataFrame) -> pd.DataFrame:
    """Run FinBERT inference on the combined text for all rows."""
    if df.empty:
        return df

    log.info("Loading FinBERT model...")
    # Load model with truncation=True to handle long texts
    sentiment_pipeline = pipeline(
        "sentiment-analysis", 
        model="ProsusAI/finbert", 
        truncation=True, 
        max_length=512,
        device_map="auto" # use GPU if available
    )

    def combine_text(row):
        title = str(row['title']) if pd.notna(row['title']) and row['title'] else ""
        body = str(row['body']) if pd.notna(row['body']) and row['body'] else ""
        if title:
            return f"{title} {body}".strip()
        return body.strip()

    log.info("Combining text...")
    texts = df.apply(combine_text, axis=1).tolist()

    log.info("Classifying %d texts in batches of %d...", len(texts), BATCH_SIZE)
    results = []
    
    # Process in batches
    for i in range(0, len(texts), BATCH_SIZE):
        batch_texts = texts[i:i + BATCH_SIZE]
        batch_results = sentiment_pipeline(batch_texts)
        results.extend(batch_results)
        if i % (BATCH_SIZE * 5) == 0 and i > 0:
            log.info("Classified %d/%d texts...", i, len(texts))
            
    df['label'] = [res['label'] for res in results]
    df['confidence_score'] = [res['score'] for res in results]

    return df


def save_results(engine, df: pd.DataFrame):
    """Write label and confidence_score back to cleaned_data."""
    if df.empty:
        return

    log.info("Saving %d results to database...", len(df))
    
    # We'll use a temporary table to do a bulk update to avoid updating row by row
    temp_table = f"temp_{TABLE}_updates"
    
    # Only keep the columns we need to update
    update_df = df[['pk', 'label', 'confidence_score']]
    
    with engine.begin() as conn:
        # Create temporary table
        update_df.to_sql(temp_table, conn, schema=SCHEMA, if_exists='replace', index=False)
        
        # Perform bulk update
        update_query = text(f"""
            UPDATE {SCHEMA}.{TABLE} t
            SET label = u.label,
                confidence_score = u.confidence_score
            FROM {SCHEMA}.{temp_table} u
            WHERE t.pk = u.pk
        """)
        conn.execute(update_query)
        
        # Drop temporary table
        conn.execute(text(f"DROP TABLE {SCHEMA}.{temp_table}"))
        
    log.info("Results saved successfully.")


def main():
    engine = get_engine()
    
    # Add columns if they don't exist
    ensure_columns(engine)
    
    # Load all rows
    df = load_data(engine)
    if df.empty:
        log.info("No data to classify.")
        return
        
    # Classify
    df = classify(df)
    
    # Save back to database
    save_results(engine, df)
    
    log.info("Classification pipeline complete.")


if __name__ == "__main__":
    main()
