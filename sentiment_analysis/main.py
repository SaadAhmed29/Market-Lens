import argparse
import logging
from datetime import datetime, timezone

from utils.db import get_engine
from sentiment_analysis.db import (
    get_connection,
    setup_schema,
    get_missing_ranges,
    check_unclassified_count
)
from sentiment_analysis.data_prep import run_prep
from sentiment_analysis.classifier import run_classification

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SCHEMA_NAME = "sentiment_data"
CLEANED_TABLE = "cleaned_data"

def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)

def main():
    parser = argparse.ArgumentParser(description="Sentiment Analysis Pipeline Runner")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    start_date = parse_date(args.start)
    end_date = parse_date(args.end)

    log.info(f"Running pipeline for date range {start_date.date()} to {end_date.date()}")

    engine = get_engine()
    conn = get_connection()

    try:
        # 1. Cleaning check
        missing_clean_ranges = get_missing_ranges(conn, SCHEMA_NAME, CLEANED_TABLE, start_date, end_date)
        if not missing_clean_ranges:
            log.info("Cleaning Check: Cleaned data already fully covers the requested date range. Skipping data prep.")
        else:
            log.info(f"Cleaning Check: Found {len(missing_clean_ranges)} missing range(s) in cleaned_data. Running data prep for missing portions.")
            for r_start, r_end in missing_clean_ranges:
                log.info(f"Running data prep for range: {r_start.date()} to {r_end.date()}")
                run_prep(engine, r_start, r_end)

        # 2. Classification check
        unclassified_count = check_unclassified_count(engine, SCHEMA_NAME, CLEANED_TABLE, start_date, end_date)
        if unclassified_count == 0:
            log.info("Classification Check: All records in the requested date range are already classified. Skipping classification.")
        else:
            log.info(f"Classification Check: Found {unclassified_count} unclassified records in the requested date range. Running classification.")
            run_classification(engine, start_date, end_date)
            
        log.info("Pipeline run completed successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
