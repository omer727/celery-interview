"""SQLite schema and connection helper.

Design decision (ADR 0007): stdlib sqlite3 with raw SQL instead of an ORM —
for a schema this small, the queries themselves are the clearest documentation
of what the API does.
"""

import contextlib
import sqlite3
from collections.abc import Iterator

# Design decision (ADR 0004): COLLATE NOCASE makes name uniqueness and type
# matching case-insensitive at the schema level, so no query has to remember
# to lower() anything. Note: SQLite's NOCASE is ASCII-only; given more time
# I'd normalize case in Python (str.casefold) for full Unicode correctness.
SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id     INTEGER PRIMARY KEY,
    name   TEXT NOT NULL UNIQUE COLLATE NOCASE,
    region TEXT NOT NULL,
    type   TEXT NOT NULL COLLATE NOCASE
);

-- Uploads are append-only (ADR 0005): rows here are only ever inserted.
CREATE TABLE IF NOT EXISTS files (
    id          INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    filename    TEXT NOT NULL
);

-- numeric_sum and search_text are derived once at upload (ADR 0003), so
-- sum_type is a single SELECT SUM and find_regions a substring scan —
-- no sheet is ever re-parsed at query time.
CREATE TABLE IF NOT EXISTS sheets (
    id          INTEGER PRIMARY KEY,
    file_id     INTEGER NOT NULL REFERENCES files(id),
    sheet_name  TEXT NOT NULL,
    csv_content TEXT NOT NULL,
    numeric_sum REAL NOT NULL,
    search_text TEXT NOT NULL
);
"""


@contextlib.contextmanager
def connect(db_path: str) -> Iterator[sqlite3.Connection]:
    """Open a connection, ensuring the schema exists (idempotent).

    Used as `with db.connect(path) as conn:` — the block is one transaction
    (commit on success, rollback on exception, as sqlite3's own context
    manager does) and the connection is always closed afterwards, which
    sqlite3's context manager alone does not do.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA)
        with conn:
            yield conn
    finally:
        conn.close()
