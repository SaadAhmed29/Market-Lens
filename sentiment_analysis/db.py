"""
Creates/migrates the `sentiment_data` schema in an existing Postgres database,
with two tables (raw_data, cleaned_data) sharing an identical column structure.
"""

import os
import logging
import psycopg2

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
    comments          JSONB,
    fetched_at        TIMESTAMPTZ DEFAULT now()
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
    "ALTER TABLE {schema}.{table} ADD COLUMN IF NOT EXISTS comments JSONB;",
    "ALTER TABLE {schema}.{table} ADD COLUMN IF NOT EXISTS fetched_at TIMESTAMPTZ DEFAULT now();",
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
    from utils.db import DB_CONFIG
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


if __name__ == "__main__":
    setup_schema()