"""StockManager: the only code that changes quantities (SDS 2.3.1).
FID-10 record damage (D'mitri) and FID-11 expired status (Janae)."""
import re
from datetime import date, datetime

from .errors import ValidationError
from .models import DamageReason
from .rules import BusinessRules

NOTE_MAX = 200                                                           # SR-10.2


class StockManager:
    def __init__(self, db, login, rules=BusinessRules, today=date.today):
        self.db, self.login, self.rules, self.today = db, login, rules, today

    # ---------- FID-10 Record damaged product (D'mitri) ----------
    def record_damage(self, user, product_id, quantity, reason, note=""):
        """Move `quantity` units of a product from In Stock to Damaged.
        Returns the remaining In Stock quantity for the product.
        Raises PermissionDenied or ValidationError({field: message}); nothing is saved on error."""
        self.login.require(user, "record_damage")                        # SR-10.1

        errors = {}                                                      # SR-10.3
        product = None
        if product_id is not None:
            rows = self.db.query("SELECT id, name FROM product WHERE id = ? AND archived = 0", (product_id,))
            product = rows[0] if rows else None
        if product is None:
            errors["product"] = "Select a product."

        text = str(quantity).strip()
        qty = int(text) if re.fullmatch(r"[0-9]+", text) else None
        if qty is None or qty < 1:
            errors["quantity"] = "Damaged quantity must be a whole number of 1 or more."

        reason_text = reason.value if isinstance(reason, DamageReason) else (reason or "")
        if reason_text not in [r.value for r in DamageReason]:
            errors["reason"] = "Select a reason."

        note = (note or "").strip()
        if len(note) > NOTE_MAX:
            errors["note"] = f"Note must be {NOTE_MAX} characters or fewer."

        batches = []
        if product is not None:
            # units come from the batch that expires first; batches with no expiry date are used last
            batches = self.db.query(
                "SELECT id, qty_in_stock FROM stock_batch WHERE product_id = ? AND qty_in_stock > 0"
                " ORDER BY expiry_date IS NULL, expiry_date, id", (product["id"],))
            available = sum(b["qty_in_stock"] for b in batches)
            if "quantity" not in errors:
                if available == 0:
                    errors["product"] = "This product has no In Stock units (it is Sold, Damaged or Expired)."
                elif qty > available:
                    errors["quantity"] = f"Only {available} unit(s) are In Stock."
        if errors:
            raise ValidationError(errors)

        now = datetime.now().isoformat(timespec="seconds")
        left = qty
        with self.db.transaction() as c:                                 # SR-10.4 to SR-10.6, SAF-2
            for b in batches:
                if left == 0:
                    break
                take = min(left, b["qty_in_stock"])
                c.execute("UPDATE stock_batch SET qty_in_stock = qty_in_stock - ?,"
                          " qty_damaged = qty_damaged + ? WHERE id = ?", (take, take, b["id"]))
                c.execute("INSERT INTO damage_record(batch_id, quantity, reason, note, performed_by, date_time)"
                          " VALUES (?,?,?,?,?,?)", (b["id"], take, reason_text, note, user.username, now))
                c.execute("INSERT INTO stock_change(batch_id, quantity, from_status, to_status, reason,"
                          " performed_by, date_time) VALUES (?,?, 'In Stock','Damaged',?,?,?)",
                          (b["id"], take, reason_text, user.username, now))
                left -= take
            c.execute("INSERT INTO audit_log(action, detail, performed_by, date_time)"
                      " VALUES ('record_damage', ?, ?, ?)",
                      (f"{product['name']}: {qty} damaged ({reason_text})", user.username, now))
        return self.in_stock_quantity(product["id"])

    def in_stock_quantity(self, product_id):
        row = self.db.query("SELECT COALESCE(SUM(qty_in_stock), 0) AS n FROM stock_batch WHERE product_id = ?",
                            (product_id,))
        return row[0]["n"]

    # ---------- FID-11 Expired status (Janae) ----------
    def expire_overdue(self, today=None):
        """Called by ExpiryTimer at start-up and every 24 hours (SR-11.1).
        Moves In Stock units of batches whose expiry date is BEFORE today to Expired.
        Stock expiring today stays In Stock (SR-11.2); no-expiry, Damaged and Sold units are never
        touched (SR-11.3, SR-11.4). All-or-nothing. Returns the number of units moved."""
        today = today or self.today()
        batches = [b for b in self.db.query(
            "SELECT b.id, b.qty_in_stock, b.expiry_date, p.name FROM stock_batch b"
            " JOIN product p ON p.id = b.product_id"
            " WHERE b.expiry_date IS NOT NULL AND b.qty_in_stock > 0")
            if self.rules.is_past_expiry(date.fromisoformat(b["expiry_date"]), today)]
        if not batches:
            return 0

        now = datetime.now().isoformat(timespec="seconds")
        moved = 0
        with self.db.transaction() as c:
            for b in batches:
                qty = b["qty_in_stock"]
                c.execute("UPDATE stock_batch SET qty_in_stock = 0, qty_expired = qty_expired + ? WHERE id = ?",
                          (qty, b["id"]))
                c.execute("INSERT INTO stock_change(batch_id, quantity, from_status, to_status, reason,"
                          " performed_by, date_time) VALUES (?,?, 'In Stock','Expired','Expired (automatic)',NULL,?)",
                          (b["id"], qty, now))
                c.execute("INSERT INTO audit_log(action, detail, performed_by, date_time)"
                          " VALUES ('expire_stock', ?, NULL, ?)",
                          (f"{b['name']}: {qty} unit(s) past expiry date {b['expiry_date']}", now))
                moved += qty
        return moved
