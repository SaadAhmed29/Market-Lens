"""
Creates/migrates the `sentiment_data` schema in an existing Postgres database,
with two tables (raw_data, cleaned_data) sharing an identical column structure.
"""

import os
import logging

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import text
from utils.db import DB_CONFIG
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SCHEMA_NAME = "sentiment_data"

# Shared column set used by both raw_data and cleaned_data.
# `pk` is an internal auto-increment id, `source_id` is Reddit's own post id.
# `date_time` is the post's creation time (used for range checks / gap
# detection in the fetcher). `comments` holds the top-N comments for the
# post as JSON.
BASE_TABLE_DDL_TEMPLATE = """
CREATE TABLE IF NOT EXISTS {schema}.{table} (
    pk                BIGSERIAL PRIMARY KEY,
    source_id         TEXT NOT NULL,
    symbol            TEXT NOT NULL,
    subreddit         TEXT,
    title             TEXT,
    body              TEXT,
    score             INTEGER,
    num_comments      INTEGER,
    date_time         TIMESTAMPTZ,
    comments          TEXT[]
);
"""

# label/confidence_score are populated later by the classification
# pipeline, and only ever live on cleaned_data — raw_data stays untouched.
LABEL_COLUMNS_DDL = [
    "ALTER TABLE {schema}.{table} ADD COLUMN IF NOT EXISTS label TEXT;",
    "ALTER TABLE {schema}.{table} ADD COLUMN IF NOT EXISTS confidence_score FLOAT;",
]

# Migration statements for the base (shared) columns — safe to run against
# a table created by an earlier version of this schema.
BASE_ALTER_STATEMENTS = [
    "ALTER TABLE {schema}.{table} ADD COLUMN IF NOT EXISTS date_time TIMESTAMPTZ;",
    "ALTER TABLE {schema}.{table} ADD COLUMN IF NOT EXISTS comments TEXT[];",
]

# If label/confidence_score were mistakenly added to raw_data by an earlier
# run of this script, drop them so raw_data matches the intended shape.
DROP_LABEL_COLUMNS_DDL = [
    "ALTER TABLE {schema}.{table} DROP COLUMN IF EXISTS label;",
    "ALTER TABLE {schema}.{table} DROP COLUMN IF EXISTS confidence_score;",
]

INDEX_DDL_TEMPLATE = """
CREATE INDEX IF NOT EXISTS idx_{table}_symbol_datetime
    ON {schema}.{table} (symbol, date_time);
"""

# Unique index (rather than a table CONSTRAINT) so it can be added with
# IF NOT EXISTS on tables that already exist. Also what ON CONFLICT
# (source_id) in the fetcher relies on for dedup.
UNIQUE_INDEX_TEMPLATE = """
CREATE UNIQUE INDEX IF NOT EXISTS ux_{table}_source_id
    ON {schema}.{table} (source_id);
"""


def get_connection():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        log.info("Connecting using DATABASE_URL")
        return psycopg2.connect(database_url)

    log.info("Connecting using DB_CONFIG from utils")
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["name"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
    )


def setup_schema():
    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            log.info("Creating schema '%s' if not exists...", SCHEMA_NAME)
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};")

            for table in ("raw_data", "cleaned_data"):
                log.info("Creating table %s.%s ...", SCHEMA_NAME, table)
                cur.execute(BASE_TABLE_DDL_TEMPLATE.format(schema=SCHEMA_NAME, table=table))

                log.info("Ensuring base columns are up to date on %s.%s ...", SCHEMA_NAME, table)
                for stmt in BASE_ALTER_STATEMENTS:
                    cur.execute(stmt.format(schema=SCHEMA_NAME, table=table))

                if table == "cleaned_data":
                    log.info("Ensuring label/confidence_score columns exist on %s.%s ...", SCHEMA_NAME, table)
                    for stmt in LABEL_COLUMNS_DDL:
                        cur.execute(stmt.format(schema=SCHEMA_NAME, table=table))
                else:
                    # raw_data should never have these — drop if a prior
                    # run of this script added them by mistake.
                    for stmt in DROP_LABEL_COLUMNS_DDL:
                        cur.execute(stmt.format(schema=SCHEMA_NAME, table=table))

                cur.execute(INDEX_DDL_TEMPLATE.format(schema=SCHEMA_NAME, table=table))
                cur.execute(UNIQUE_INDEX_TEMPLATE.format(schema=SCHEMA_NAME, table=table))

        log.info("Schema setup complete: %s.raw_data, %s.cleaned_data", SCHEMA_NAME, SCHEMA_NAME)
    finally:
        conn.close()

# Data Operations Helpers

def get_existing_range(conn, schema, table, symbol=None):
    """Return (min_date_time, max_date_time) already stored, optionally for a specific symbol."""
    if symbol:
        query = f"SELECT MIN(date_time), MAX(date_time) FROM {schema}.{table} WHERE symbol = %s"
        with conn.cursor() as cur:
            cur.execute(query, (symbol,))
            return cur.fetchone()
    else:
        query = f"SELECT MIN(date_time), MAX(date_time) FROM {schema}.{table}"
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchone()

def get_missing_ranges(conn, schema, table, start, end, symbol=None):
    """Compare the requested [start, end] window against what's already stored."""
    existing_min, existing_max = get_existing_range(conn, schema, table, symbol)

    if existing_min is None:
        return [(start, end)]

    missing = []
    if start < existing_min:
        missing.append((start, min(existing_min, end)))
    if end > existing_max:
        missing.append((max(existing_max, start), end))

    if not missing:
        msg = f"Symbol {symbol}: " if symbol else ""
        log.info(
            "%srequested range %s -> %s already covered by stored data (%s -> %s), skipping.",
            msg, start.date() if hasattr(start, 'date') else start, end.date() if hasattr(end, 'date') else end, 
            existing_min.date() if hasattr(existing_min, 'date') else existing_min, 
            existing_max.date() if hasattr(existing_max, 'date') else existing_max
        )
    return missing

def save_raw_items(conn, items: list, symbol: str, schema: str, table: str):
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
            item["comments"],
        )
        for item in items
    ]

    query = f"""
        INSERT INTO {schema}.{table}
        (source_id, symbol, subreddit, title, body, score, num_comments,
         date_time, comments)
        VALUES %s
        ON CONFLICT (source_id) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, query, rows)
    conn.commit()

def load_raw_data(engine, schema, table, start_date=None, end_date=None) -> pd.DataFrame:
    """Read rows from raw_data, optionally filtered by date range."""
    query = f"SELECT * FROM {schema}.{table}"
    params = {}
    
    if start_date and end_date:
        query += " WHERE date_time >= %(start)s AND date_time <= %(end)s"
        params = {"start": start_date, "end": end_date}
        
    df = pd.read_sql(query, engine, params=params)
    log.info("Loaded %d rows from %s.%s", len(df), schema, table)
    return df

def _upsert_on_conflict(table, conn, keys, data_iter):
    """Custom to_sql insert method: ON CONFLICT (source_id) DO NOTHING."""
    data = [dict(zip(keys, row)) for row in data_iter]
    stmt = pg_insert(table.table).values(data)
    stmt = stmt.on_conflict_do_nothing(index_elements=["source_id"])
    conn.execute(stmt)

def save_cleaned_data(engine, df: pd.DataFrame, schema: str, table: str) -> None:
    """Write cleaned rows into the cleaned_data table."""
    cols = [c for c in df.columns if c != "pk"]
        
    df[cols].to_sql(
        table,
        engine,
        schema=schema,
        if_exists="append",
        index=False,
        method=_upsert_on_conflict,
    )
    log.info("Saved %d rows to %s.%s", len(df), schema, table)

def load_unclassified_data(engine, schema, table, start_date=None, end_date=None) -> pd.DataFrame:
    """Read rows from cleaned_data that lack a label, optionally within a date range."""
    query = f"SELECT pk, title, body, comments FROM {schema}.{table} WHERE label IS NULL"
    params = {}
    if start_date and end_date:
        query += " AND date_time >= %(start)s AND date_time <= %(end)s"
        params = {"start": start_date, "end": end_date}
        
    query += " ORDER BY pk"
    df = pd.read_sql(query, engine, params=params)
    log.info("Loaded %d unclassified rows from %s.%s", len(df), schema, table)
    return df

def save_classification_results(engine, df: pd.DataFrame, schema: str, table: str):
    """Write label and confidence_score back to cleaned_data."""
    if df.empty:
        return

    log.info("Saving %d results to database...", len(df))
    temp_table = f"temp_{table}_updates"
    update_df = df[['pk', 'label', 'confidence_score']]
    
    with engine.begin() as conn:
        update_df.to_sql(temp_table, conn, schema=schema, if_exists='replace', index=False)
        update_query = text(f"""
            UPDATE {schema}.{table} t
            SET label = u.label,
                confidence_score = u.confidence_score
            FROM {schema}.{temp_table} u
            WHERE t.pk = u.pk
        """)
        conn.execute(update_query)
        conn.execute(text(f"DROP TABLE {schema}.{temp_table}"))
        
    log.info("Results saved successfully.")

def check_unclassified_count(engine, schema, table, start_date, end_date) -> int:
    """Count how many rows have a NULL label in the given date range."""
    query = text(f"""
        SELECT COUNT(*) FROM {schema}.{table} 
        WHERE label IS NULL 
        AND date_time >= :start AND date_time <= :end
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"start": start_date, "end": end_date}).scalar()
    return result

if __name__ == "__main__":
    setup_schema()