"""StockManager: the only code that changes quantities (SDS 2.3.1).
FID-10 record damage (D'mitri, TODO) and FID-11 expired status (Janae, TODO)."""
from datetime import date

from .rules import BusinessRules


class StockManager:
    def __init__(self, db, login, rules=BusinessRules, today=date.today):
        self.db, self.login, self.rules, self.today = db, login, rules, today

    # ---------- FID-10 Record damaged product (D'mitri) ----------
    def record_damage(self, user, product_id, quantity, reason, note=""):
        """TODO (D'mitri) FID-10, SR-10.1 to SR-10.7.
        - require(user, 'record_damage'); reject no product / not In Stock / bad quantity /
          quantity above In Stock / reason not in DamageReason / note over 200 characters.
        - If a product has several batches, take units from the batch that expires first.
        - In ONE transaction: move qty from In Stock to Damaged, write a damage_record row,
          a stock_change row and an audit_log row. Product shows Damaged when no usable units remain.
        - Return the remaining In Stock quantity."""
        raise NotImplementedError("FID-10 Record Damage - owner: D'mitri")

    # ---------- FID-11 Expired status (Janae) ----------
    def expire_overdue(self, today=None):
        """TODO (Janae) FID-11, SR-11.1 to SR-11.4. Called by ExpiryTimer.
        - Find batches with expiry_date < today and qty_in_stock > 0 (BusinessRules.is_past_expiry).
        - In ONE transaction: move those units from In Stock to Expired, write stock_change rows and
          audit_log rows with performed_by = NULL (automatic event, SEC-4).
        - Stock expiring TODAY stays In Stock. Damaged and Sold units are never touched.
        - Return the number of units moved."""
        raise NotImplementedError("FID-11 Expired status - owner: Janae")
