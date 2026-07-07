"""
Creates the `sentiment_data` schema in an existing Postgres database, with
two tables (raw_data, cleaned_data) sharing an identical column structure.
"""

import os
import logging
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SCHEMA_NAME = "sentiment_data"

# Shared column definition used by both raw_data and cleaned_data.
# `pk` is an internal auto-increment id.
TABLE_DDL_TEMPLATE = """
CREATE TABLE IF NOT EXISTS {schema}.{table} (
    pk              BIGSERIAL PRIMARY KEY,
    symbol          TEXT NOT NULL,
    subreddit       TEXT,
    title           TEXT,
    body            TEXT,
    score           INTEGER,
    num_comments    INTEGER
);
"""

INDEX_DDL_TEMPLATE = """
CREATE INDEX IF NOT EXISTS idx_{table}_symbol
    ON {schema}.{table} (symbol);
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
                cur.execute(TABLE_DDL_TEMPLATE.format(schema=SCHEMA_NAME, table=table))
                cur.execute(INDEX_DDL_TEMPLATE.format(schema=SCHEMA_NAME, table=table))

        log.info("Schema setup complete: %s.raw_data, %s.cleaned_data", SCHEMA_NAME, SCHEMA_NAME)
    finally:
        conn.close()


if __name__ == "__main__":
    setup_schema()