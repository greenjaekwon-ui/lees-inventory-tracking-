"""Database class: the ONLY code that touches the data file (SEC-5)."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


class Database:
    def __init__(self, path=":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA.read_text(encoding="utf-8"))

    @contextmanager
    def transaction(self):
        """All-or-nothing (SAF-2, QA-2): commit if the block finishes,
        roll everything back if anything inside raises."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def query(self, sql, params=()):
        """Always pass values through `params` (the ? placeholders) so search text
        is treated as data and never as SQL (SEC-6)."""
        return self.conn.execute(sql, params).fetchall()

    def close(self):
        self.conn.close()
