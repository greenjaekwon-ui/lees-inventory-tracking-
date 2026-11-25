"""Database class: the ONLY code that touches the data file (SEC-5)."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


class Database:
    def __init__(self, path=":memory:"):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        self._upgrade_sale_table()

    def _upgrade_sale_table(self):
        """Older data files made sale_ref UNIQUE on its own, which stops one sale using stock from two
        expiry-date groups. Rebuild the table once with UNIQUE(sale_ref, batch_id)."""
        row = self.conn.execute("SELECT sql FROM sqlite_master WHERE name = 'sale'").fetchone()
        if row and "sale_ref TEXT NOT NULL UNIQUE" in row["sql"]:
            self.conn.executescript("""
                ALTER TABLE sale RENAME TO sale_old;
                CREATE TABLE sale (
                    id INTEGER PRIMARY KEY,
                    sale_ref TEXT NOT NULL,
                    batch_id INTEGER NOT NULL REFERENCES stock_batch(id),
                    quantity INTEGER NOT NULL CHECK (quantity > 0),
                    performed_by TEXT, date_time TEXT NOT NULL,
                    UNIQUE (sale_ref, batch_id));
                INSERT INTO sale SELECT id, sale_ref, batch_id, quantity, performed_by, date_time FROM sale_old;
                DROP TABLE sale_old;""")
            self.conn.commit()

    def backup(self, folder, keep=7):
        """Copy the data file to folder/lees_inventory_backup_<date-time>.db using SQLite's own backup
        (safe while the database is open). Keeps the newest `keep` backups. Returns the new file's path
        (SDS Database.backup, SAF-3)."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"lees_inventory_backup_{datetime.now():%Y%m%d_%H%M%S_%f}.db"
        dest = sqlite3.connect(str(target))
        try:
            self.conn.backup(dest)
        finally:
            dest.close()
        for old in sorted(folder.glob("lees_inventory_backup_*.db"))[:-keep]:
            old.unlink()
        return target

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
