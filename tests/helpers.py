"""Shared test set-up: an in-memory database, the managers, one user per role, and a clock fixed to TODAY."""
from datetime import date, timedelta

from app.data.database import Database
from app.logic.alert_manager import AlertManager
from app.logic.login_manager import LoginManager
from app.logic.models import Role, User
from app.logic.product_manager import ProductManager
from app.logic.stock_manager import StockManager

TODAY = date(2026, 11, 23)


class Env:
    """env.pm / env.sm / env.am are the managers; env.mgr, env.owner, env.wh, env.cash are users."""

    def __init__(self, today=TODAY):
        self.today = today
        self.db = Database()
        login = LoginManager(self.db)
        clock = lambda: self.today
        self.pm = ProductManager(self.db, login, today=clock)
        self.sm = StockManager(self.db, login, today=clock)
        self.am = AlertManager(self.db, login, today=clock)
        self.mgr = User(1, "mgr", Role.INVENTORY_MANAGER)
        self.owner = User(2, "owner", Role.OWNER)
        self.wh = User(3, "wh", Role.WAREHOUSE)
        self.cash = User(4, "cash", Role.CASHIER)

    def add(self, name, qty, threshold=0, days=None):
        """Add a product through FID-1; `days` = days from today until expiry (None = no expiry)."""
        expiry = (self.today + timedelta(days=days)).isoformat() if days is not None else None
        if days is not None and days < 0:               # FID-1 rejects past dates, so insert directly
            pid = self.add(name, qty, threshold)
            self.db.conn.execute("UPDATE stock_batch SET expiry_date = ? WHERE product_id = ?", (expiry, pid))
            self.db.conn.commit()
            return pid
        return self.pm.add_product(self.mgr, name, qty, expiry, threshold)

    def add_batch(self, product_id, qty, days):
        """A second batch for an existing product."""
        expiry = (self.today + timedelta(days=days)).isoformat()
        self.db.conn.execute("INSERT INTO stock_batch(product_id, expiry_date, qty_in_stock) VALUES (?,?,?)",
                             (product_id, expiry, qty))
        self.db.conn.commit()

    def batch(self, product_id):
        return [dict(r) for r in self.db.query("SELECT * FROM stock_batch WHERE product_id = ? ORDER BY id",
                                               (product_id,))]

    def count(self, table):
        return self.db.query(f"SELECT COUNT(*) n FROM {table}")[0]["n"]

    def status(self, product_id):
        return [r["status"] for r in self.pm.list_batches(self.mgr) if r["product_id"] == product_id]

    def close(self):
        self.db.close()
