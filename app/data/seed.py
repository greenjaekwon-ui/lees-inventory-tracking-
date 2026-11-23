"""Seed users, and optional demo data used by everyone's tests and the demo.
    python -m app.data.seed --demo        (adds demo products to lees_inventory.db)
Demo products are dated relative to today so the boundary cases always work."""
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from app.data.database import Database
from app.logic.login_manager import LoginManager
from app.logic.models import Role

USERS = [("manager", "manager123", Role.INVENTORY_MANAGER),
         ("owner", "owner123", Role.OWNER),
         ("warehouse", "warehouse123", Role.WAREHOUSE),
         ("cashier", "cashier123", Role.CASHIER)]


def ensure_seed(db):
    if db.query("SELECT 1 FROM user LIMIT 1"):
        return
    login = LoginManager(db)
    for username, password, role in USERS:
        login.create_user(username, password, role)


def add_demo_data(db, today=None):
    """(name, in_stock, threshold, days_until_expiry or None)"""
    today = today or date.today()
    demo = [
        ("Rice 5kg",       4, 5, None),   # LOW STOCK (below threshold)             FID-5
        ("Sugar 2kg",      3, 3, None),   # LOW STOCK (exactly at threshold)        FID-5 boundary
        ("Flour 1kg",     50, 10, None),  # normal, no expiry                       FID-5/6 negative
        ("Milk 1L",       20, 5, 10),     # nearing expiry (10 days)                FID-6
        ("Yogurt 500g",    8, 2, 30),     # nearing expiry (exactly 30 days)        FID-6 boundary
        ("Cheese 250g",    6, 2, 31),     # NOT nearing (31 days)                   FID-6 boundary
        ("Butter 250g",    9, 2, 0),      # expires TODAY: still In Stock           FID-11 boundary
        ("Juice 1L",      12, 4, -2),     # expired 2 days ago -> should expire     FID-11
    ]
    now = datetime.now().isoformat(timespec="seconds")
    with db.transaction() as c:
        for name, qty, threshold, days in demo:
            if c.execute("SELECT 1 FROM product WHERE name = ?", (name,)).fetchone():
                continue
            pid = c.execute("INSERT INTO product(name, low_stock_level) VALUES (?,?)",
                            (name, threshold)).lastrowid
            exp = (today + timedelta(days=days)).isoformat() if days is not None else None
            c.execute("INSERT INTO stock_batch(product_id, expiry_date, qty_in_stock) VALUES (?,?,?)",
                      (pid, exp, qty))
            c.execute("INSERT INTO audit_log(action, detail, performed_by, date_time) VALUES ('demo_seed', ?, NULL, ?)",
                      (name, now))


if __name__ == "__main__":
    path = Path(__file__).resolve().parents[2] / "lees_inventory.db"
    database = Database(str(path))
    ensure_seed(database)
    if "--demo" in sys.argv:
        add_demo_data(database)
        print("Demo data added to", path)
    else:
        print("Users ready in", path, "(add --demo for sample products)")
