"""AlertManager: alerts are computed from current stock, not stored (SDS 3.2.1).
FID-5 low stock (Ricardo) and FID-6 nearing expiry (Tevin)."""
from datetime import date

from .rules import BusinessRules

UNKNOWN_PRODUCT = "Unknown Product"


class AlertManager:
    def __init__(self, db, login, rules=BusinessRules, today=date.today):
        self.db, self.login, self.rules, self.today = db, login, rules, today

    # ---------- FID-5 Low-stock alert (Ricardo) ----------
    def low_stock_alerts(self, user):
        """Products whose In Stock quantity is equal to or below their low-stock level.
        Only In Stock units count (Sold, Damaged and Expired units do not). Archived products are
        ignored. Stock that points at a product that no longer exists is listed as 'Unknown Product'
        with no level, so staff notice the broken record (UC 05 alternate flow).
        Returns [{'product_id', 'name', 'in_stock', 'threshold'}]."""
        self.login.require(user, "view_alerts")                          # SR-5.1
        rows = self.db.query(
            "SELECT b.product_id AS product_id, p.name AS name, p.low_stock_level AS threshold,"
            " SUM(b.qty_in_stock) AS in_stock"
            " FROM stock_batch b LEFT JOIN product p ON p.id = b.product_id"
            " WHERE p.id IS NULL OR p.archived = 0"
            " GROUP BY b.product_id ORDER BY p.name")
        alerts = []
        for r in rows:
            if r["name"] is None:                                        # SR-5.2 unknown product
                alerts.append({"product_id": r["product_id"], "name": UNKNOWN_PRODUCT,
                               "in_stock": r["in_stock"], "threshold": None})
            elif self.rules.is_low_stock(r["in_stock"], r["threshold"]):  # SR-5.3, SR-5.4
                alerts.append({"product_id": r["product_id"], "name": r["name"],
                               "in_stock": r["in_stock"], "threshold": r["threshold"]})
        return alerts

    # ---------- FID-6 Nearing-expiry notification (Tevin) ----------
    def nearing_expiry_notifications(self, user):
        """One entry per batch that still has In Stock units and expires 0 to 30 days from today.
        Stock with no expiry date, units that are Sold/Damaged/Expired, expired batches (already past
        their date) and archived products are ignored. Sorted soonest first.
        Returns [{'product_id', 'name', 'quantity', 'expiry_date', 'days_left'}]."""
        self.login.require(user, "view_alerts")                          # SR-6.1
        today = self.today()
        rows = self.db.query(
            "SELECT p.id AS product_id, p.name, b.qty_in_stock AS quantity, b.expiry_date"
            " FROM stock_batch b JOIN product p ON p.id = b.product_id"
            " WHERE p.archived = 0 AND b.qty_in_stock > 0 AND b.expiry_date IS NOT NULL"
            " ORDER BY b.expiry_date, p.name")
        notes = []
        for r in rows:
            expiry = date.fromisoformat(r["expiry_date"])
            if self.rules.is_nearing_expiry(expiry, today):              # SR-6.2
                notes.append({"product_id": r["product_id"], "name": r["name"], "quantity": r["quantity"],
                              "expiry_date": r["expiry_date"], "days_left": (expiry - today).days})
        return notes
