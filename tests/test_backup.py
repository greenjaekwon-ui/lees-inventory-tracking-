"""Database backup (SAF-3)."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tests.helpers import Env

class T(unittest.TestCase):
    def setUp(self):
        self.e = Env()
        self.addCleanup(self.e.close)
        self.e.add("Rice 5kg", 10, 3)

    def test_backup_file_contains_the_data(self):
        """backup file contains the data"""
        with tempfile.TemporaryDirectory() as folder:
            path = self.e.db.backup(folder)
            copy = sqlite3.connect(str(path))
            self.assertEqual(copy.execute("SELECT COUNT(*) FROM product").fetchone()[0], 1)
            copy.close()

    def test_only_the_newest_backups_are_kept(self):
        """only the newest backups are kept"""
        with tempfile.TemporaryDirectory() as folder:
            for _ in range(9):
                self.e.db.backup(folder, keep=7)
            self.assertEqual(len(list(Path(folder).glob("lees_inventory_backup_*.db"))), 7)


