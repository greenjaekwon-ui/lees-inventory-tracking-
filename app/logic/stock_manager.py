"""StockManager: the only code that changes quantities (SDS 2.3.1).
FID-10 record damage (D'mitri), FID-11 expired status (Janae), FID-4 stock changes and FID-9 sales."""
import re
import sqlite3
from datetime import date, datetime

from .errors import ValidationError
from .models import ChangeType, DamageReason
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

    # ---------- FID-4 Stock changes ----------
    def change_stock(self, user, product_id, change_type, quantity, reason, batch_id=None, expiry=None):
        """Record stock received (quantity 1 or more) or a count correction (a whole number, plus or
        minus, not zero). Returns the product's new In Stock quantity. Raises PermissionDenied or
        ValidationError({field: message}); a rejected change saves and logs nothing (SR-4.2, AC-4.5).
        Received stock and increases go to `batch_id`, or to the batch with the given expiry date (a new
        batch if there is none), or to the product's only batch. Decreases come from the batch that
        expires first, unless `batch_id` is given."""
        self.login.require(user, "change_stock")                         # SR-4.1
        errors = {}
        product = None
        if product_id is not None:
            rows = self.db.query("SELECT id, name FROM product WHERE id = ? AND archived = 0", (product_id,))
            product = rows[0] if rows else None
        if product is None:
            errors["product"] = "Select a product."

        kind = change_type.value if isinstance(change_type, ChangeType) else (change_type or "")
        if kind not in (ChangeType.STOCK_RECEIVED.value, ChangeType.COUNT_CORRECTION.value):
            errors["change_type"] = "Choose Stock received or Count correction."
        text = str(quantity).strip()
        qty = None
        if kind == ChangeType.STOCK_RECEIVED.value:                      # SR-4.2
            qty = int(text) if re.fullmatch(r"[0-9]+", text) and int(text) >= 1 else None
            if qty is None:
                errors["quantity"] = "Quantity received must be a whole number of 1 or more."
        elif kind == ChangeType.COUNT_CORRECTION.value:
            qty = int(text) if re.fullmatch(r"[+-]?[0-9]+", text) and int(text) != 0 else None
            if qty is None:
                errors["quantity"] = "Enter the correction as a whole number other than 0 (for example -5 or 5)."
        reason = (reason or "").strip()
        if not reason:
            errors["reason"] = "Enter a reason."
        elif len(reason) > 200:
            errors["reason"] = "Reason must be 200 characters or fewer."

        exp = None
        if expiry not in (None, ""):
            try:
                exp = datetime.strptime(str(expiry).strip(), "%Y-%m-%d").date()
                if exp < self.today() and qty is not None and qty > 0:
                    errors["expiry"] = "Expiry date cannot be earlier than today."
            except ValueError:
                errors["expiry"] = "Enter a valid date (YYYY-MM-DD)."
        if errors:
            raise ValidationError(errors)

        batches = self.db.query("SELECT id, expiry_date, qty_in_stock FROM stock_batch WHERE product_id = ?"
                                " ORDER BY expiry_date IS NULL, expiry_date, id", (product["id"],))
        if batch_id is not None and batch_id not in [b["id"] for b in batches]:
            raise ValidationError({"batch": "Batch not found for this product."})
        available = sum(b["qty_in_stock"] for b in batches if batch_id in (None, b["id"]))
        if qty < 0 and -qty > available:                                 # In Stock may never go below zero
            raise ValidationError({"quantity": f"Only {available} unit(s) are In Stock, so the stock cannot be reduced by {-qty}."})

        target = None
        if qty > 0:
            if batch_id is not None:
                target = batch_id
            elif exp is not None:
                same = [b for b in batches if b["expiry_date"] == exp.isoformat()]
                target = same[0]["id"] if same else None                 # None = create a new batch
            elif len(batches) == 1:
                target = batches[0]["id"]
            elif batches and not any(b["expiry_date"] is None for b in batches):
                raise ValidationError({"batch": "This product has several expiry-date groups: enter the expiry date or choose a batch."})
            else:
                target = next((b["id"] for b in batches if b["expiry_date"] is None), None)

        now = datetime.now().isoformat(timespec="seconds")
        with self.db.transaction() as c:                                 # SR-4.3, SR-4.5, SAF-2
            if qty > 0:
                if target is None:
                    target = c.execute("INSERT INTO stock_batch(product_id, expiry_date, qty_in_stock) VALUES (?,?,0)",
                                       (product["id"], exp.isoformat() if exp else None)).lastrowid
                c.execute("UPDATE stock_batch SET qty_in_stock = qty_in_stock + ? WHERE id = ?", (qty, target))
                c.execute("INSERT INTO stock_change(batch_id, quantity, from_status, to_status, reason,"
                          " performed_by, date_time) VALUES (?,?,NULL,'In Stock',?,?,?)",
                          (target, qty, f"{kind}: {reason}", user.username, now))
            else:
                left = -qty
                for b in batches:
                    if left == 0:
                        break
                    if batch_id not in (None, b["id"]) or b["qty_in_stock"] == 0:
                        continue
                    take = min(left, b["qty_in_stock"])
                    c.execute("UPDATE stock_batch SET qty_in_stock = qty_in_stock - ? WHERE id = ?", (take, b["id"]))
                    c.execute("INSERT INTO stock_change(batch_id, quantity, from_status, to_status, reason,"
                              " performed_by, date_time) VALUES (?,?,'In Stock',NULL,?,?,?)",
                              (b["id"], take, f"{kind}: {reason}", user.username, now))
                    left -= take
            c.execute("INSERT INTO audit_log(action, detail, performed_by, date_time) VALUES ('change_stock', ?, ?, ?)",
                      (f"{product['name']}: {kind} {qty:+d} ({reason})", user.username, now))
        return self.in_stock_quantity(product["id"])                     # SR-4.6: alerts are worked out when viewed

    # ---------- FID-9 Record a sale ----------
    def record_sale(self, user, product_id, quantity, sale_ref, batch_id=None):
        """Move `quantity` units from In Stock to Sold for one sale. Returns the product's remaining In Stock
        quantity. Eligible stock = In Stock units whose expiry date has not passed, checked again at save
        time (SR9.3). Units come from the batch that expires first. A sale reference can be used once
        (SR9.4). All-or-nothing; raises PermissionDenied or ValidationError({field: message})."""
        self.login.require(user, "record_sale")                          # SR9.1
        errors = {}
        ref = str(sale_ref or "").strip()
        if not ref:
            errors["sale_ref"] = "Enter a sale reference."
        elif self.db.query("SELECT 1 FROM sale WHERE sale_ref = ?", (ref,)):
            errors["sale_ref"] = "This sale reference was already recorded. Stock was not deducted again."
        product = None
        if product_id is not None:
            rows = self.db.query("SELECT id, name FROM product WHERE id = ? AND archived = 0", (product_id,))
            product = rows[0] if rows else None
        if product is None:
            errors["product"] = "Select an active product."
        text = str(quantity).strip()
        qty = int(text) if re.fullmatch(r"[0-9]+", text) and int(text) >= 1 else None
        if qty is None:
            errors["quantity"] = "Quantity sold must be a whole number of 1 or more."

        eligible = []
        if product is not None:
            today = self.today()
            for b in self.db.query(
                    "SELECT id, expiry_date, qty_in_stock FROM stock_batch WHERE product_id = ? AND qty_in_stock > 0"
                    " ORDER BY expiry_date IS NULL, expiry_date, id", (product["id"],)):
                if batch_id not in (None, b["id"]):
                    continue
                if b["expiry_date"] is not None and self.rules.is_past_expiry(date.fromisoformat(b["expiry_date"]), today):
                    continue                                             # expired between opening the screen and saving
                eligible.append(b)
            available = sum(b["qty_in_stock"] for b in eligible)
            if "quantity" not in errors:
                if available == 0:
                    errors["product"] = "No eligible stock: the units are Sold, Damaged, Expired or past their expiry date."
                elif qty > available:
                    errors["quantity"] = f"Only {available} unit(s) are available for sale."
        if errors:
            raise ValidationError(errors)

        now = datetime.now().isoformat(timespec="seconds")
        left = qty
        try:
            with self.db.transaction() as c:                             # SR9.2, SR9.4, SAF-2
                for b in eligible:
                    if left == 0:
                        break
                    take = min(left, b["qty_in_stock"])
                    c.execute("UPDATE stock_batch SET qty_in_stock = qty_in_stock - ?, qty_sold = qty_sold + ?"
                              " WHERE id = ?", (take, take, b["id"]))
                    c.execute("INSERT INTO sale(sale_ref, batch_id, quantity, performed_by, date_time)"
                              " VALUES (?,?,?,?,?)", (ref, b["id"], take, user.username, now))
                    c.execute("INSERT INTO stock_change(batch_id, quantity, from_status, to_status, reason,"
                              " performed_by, date_time) VALUES (?,?,'In Stock','Sold',?,?,?)",
                              (b["id"], take, f"Sale {ref}", user.username, now))
                    left -= take
                c.execute("INSERT INTO audit_log(action, detail, performed_by, date_time) VALUES ('record_sale', ?, ?, ?)",
                          (f"{product['name']}: {qty} sold (ref {ref})", user.username, now))
        except sqlite3.IntegrityError:
            raise ValidationError({"sale_ref": "This sale reference was already recorded. Stock was not deducted again."})
        return self.in_stock_quantity(product["id"])
