"""
Reads cleaned posts from sentiment_data.cleaned_data, classifies them using FinBERT,
and writes the results (label and confidence_score) back to the same table.
"""


import logging
import pandas as pd
from transformers import pipeline
from utils.db import get_engine
from sentiment_analysis.db import load_unclassified_data, save_classification_results

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

SCHEMA = "sentiment_data"
TABLE = "cleaned_data"
BATCH_SIZE = 128


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
        t_val = row.get('title')
        title = str(t_val).strip() if t_val is not None and not (isinstance(t_val, float) and pd.isna(t_val)) and str(t_val).strip() else ""
        
        b_val = row.get('body')
        body = str(b_val).strip() if b_val is not None and not (isinstance(b_val, float) and pd.isna(b_val)) and str(b_val).strip() else ""
        
        parts = [
            f"post: {title}" if title else "post:",
            f"body: {body}" if body else "body:"
        ]
        
        comments_val = row.get('comments')
        try:
            if hasattr(comments_val, 'tolist'):
                comments = comments_val.tolist()
            elif isinstance(comments_val, list):
                comments = comments_val
            else:
                comments = []
                
            if isinstance(comments, (list, tuple)):
                for i, c in enumerate(comments, 1):
                    if isinstance(c, str):
                        c_body = c.strip()
                        if c_body:
                            parts.append(f"comment{i}: {c_body}")
                        else:
                            parts.append(f"comment{i}:")
        except Exception:
            pass
                
        return " ".join(parts).replace('\n', ' ').replace('\r', ' ')

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


def run_classification(engine, start_date=None, end_date=None):
    df = load_unclassified_data(engine, SCHEMA, TABLE, start_date, end_date)
    if df.empty:
        log.info("No unclassified data in the given date range.")
        return
        
    df = classify(df)
    save_classification_results(engine, df, SCHEMA, TABLE)
    log.info("Classification step complete.")


def main():
    engine = get_engine()
    run_classification(engine)

if __name__ == "__main__":
    main()
