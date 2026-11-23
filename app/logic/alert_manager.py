"""AlertManager: alerts are computed from current stock, not stored (SDS 3.2.1).
FID-5 low stock (Ricardo, TODO) and FID-6 nearing expiry (Tevin, TODO)."""
from datetime import date

from .rules import BusinessRules


class AlertManager:
    def __init__(self, db, login, rules=BusinessRules, today=date.today):
        self.db, self.login, self.rules, self.today = db, login, rules, today

    # ---------- FID-5 Low-stock alert (Ricardo) ----------
    def low_stock_alerts(self, user):
        """TODO (Ricardo) FID-5, SR-5.1 to SR-5.4.
        - require(user, 'view_alerts').
        - Count only In Stock units per product (sum of qty_in_stock over its batches),
          compare with low_stock_level using BusinessRules.is_low_stock (equal or below).
        - Return a list of dicts: {'product_id', 'name', 'in_stock', 'threshold'}."""
        raise NotImplementedError("FID-5 Low-stock alert - owner: Ricardo")

    # ---------- FID-6 Nearing-expiry notification (Tevin) ----------
    def nearing_expiry_notifications(self, user):
        """TODO (Tevin) FID-6, SR-6.1 to SR-6.4.
        - require(user, 'view_alerts').
        - Batches with qty_in_stock > 0 and an expiry date 0 to 30 days from today
          (BusinessRules.is_nearing_expiry). Ignore no-expiry stock and Sold/Damaged/Expired units.
        - Return a list of dicts: {'product_id', 'name', 'quantity', 'expiry_date'} (one per batch)."""
        raise NotImplementedError("FID-6 Nearing-expiry notification - owner: Tevin")
