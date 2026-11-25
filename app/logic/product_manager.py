"""ProductManager. FID-1 add (Jaekwon), FID-3 update (Brandon), FID-2 remove and FID-7 search."""
import re
from datetime import date, datetime

from .errors import DuplicateProductError, ValidationError
from .rules import BusinessRules


STATUS_LABELS = ("In Stock", "Low Stock", "Out of Stock", "Sold", "Damaged", "Expired")   # FID-7 AC-7.1


def _whole_number(value):
    """Return int if value is a whole number of 0 or more, else None."""
    text = str(value).strip()
    return int(text) if re.fullmatch(r"[0-9]+", text) else None


class ProductManager:
    def __init__(self, db, login, rules=BusinessRules, today=date.today):
        self.db, self.login, self.rules, self.today = db, login, rules, today

    # ---------- FID-1 Add Product (Jaekwon) ----------
    def add_product(self, user, name, quantity, expiry=None, threshold=0):
        """Returns the new product id. Raises PermissionDenied,
        ValidationError({field: message}) or DuplicateProductError."""
        self.login.require(user, "add_product")                          # SR-1.1

        errors, today = {}, self.today()                                 # SR-1.3
        name = (name or "").strip()
        if not name:
            errors["name"] = "Product name is required."
        qty = _whole_number(quantity)
        if qty is None:
            errors["quantity"] = "Quantity must be a whole number of 0 or more."
        low_level = _whole_number(threshold if str(threshold).strip() != "" else 0)
        if low_level is None:
            errors["threshold"] = "Low-stock level must be a whole number of 0 or more."
        exp = None
        if expiry not in (None, ""):
            try:
                exp = datetime.strptime(str(expiry).strip(), "%Y-%m-%d").date()
                if not self.rules.is_valid_new_expiry(exp, today):       # today OK, earlier rejected
                    errors["expiry"] = "Expiry date cannot be earlier than today."
            except ValueError:
                errors["expiry"] = "Enter a valid date (YYYY-MM-DD)."
        if errors:
            raise ValidationError(errors)

        if self.db.query("SELECT 1 FROM product WHERE name = ?", (name,)):   # SR-1.4
            raise DuplicateProductError(f"'{name}' already exists.")

        now = datetime.now().isoformat(timespec="seconds")
        with self.db.transaction() as c:                                 # SR-1.5, SAF-2
            pid = c.execute("INSERT INTO product(name, low_stock_level) VALUES (?, ?)",
                            (name, low_level)).lastrowid
            bid = c.execute("INSERT INTO stock_batch(product_id, expiry_date, qty_in_stock) VALUES (?,?,?)",
                            (pid, exp.isoformat() if exp else None, qty)).lastrowid
            c.execute("INSERT INTO stock_change(batch_id, quantity, from_status, to_status, reason, performed_by, date_time)"
                      " VALUES (?,?,NULL,'In Stock','Stock received (new product)',?,?)",
                      (bid, qty, user.username, now))
            c.execute("INSERT INTO audit_log(action, detail, performed_by, date_time) VALUES ('add_product', ?, ?, ?)",
                      (name, user.username, now))
        return pid

    # ---------- shared read helpers (Jaekwon) ----------
    def list_batches(self, user):
        """One dict per stock batch, for the product table (includes the batch status)."""
        self.login.require(user, "view_products")
        rows = self.db.query(
            "SELECT p.id AS product_id, p.name, p.low_stock_level AS threshold, b.id AS batch_id,"
            " b.expiry_date, b.qty_in_stock, b.qty_sold, b.qty_damaged, b.qty_expired,"
            " (SELECT sc.to_status FROM stock_change sc WHERE sc.batch_id = b.id"
            "  ORDER BY sc.id DESC LIMIT 1) AS last_status"
            " FROM product p JOIN stock_batch b ON b.product_id = p.id"
            " WHERE p.archived = 0 ORDER BY p.name, b.expiry_date")
        result = []
        for r in rows:
            d = dict(r)
            d["status"] = self.rules.batch_status(d["qty_in_stock"], d.pop("last_status"))
            result.append(d)
        return result

    def list_products(self, user):
        """(id, name) pairs for drop-down lists."""
        self.login.require(user, "view_products")
        return [(r["id"], r["name"]) for r in
                self.db.query("SELECT id, name FROM product WHERE archived = 0 ORDER BY name")]

    # ---------- FID-3 Update Product (Brandon) ----------
    def get_product_details(self, user, product_id, batch_id=None):
        """Details for the update form (SR-3.2). A product with no expiry date gives expiry_date None
        (shown as a blank field). If the product has several batches, pass batch_id."""
        self.login.require(user, "update_product")                       # SR-3.1
        batch = self._find_batch(product_id, batch_id)
        row = self.db.query("SELECT id, name, low_stock_level FROM product WHERE id = ?", (product_id,))[0]
        return {"product_id": row["id"], "name": row["name"], "threshold": row["low_stock_level"],
                "batch_id": batch["id"] if batch else None,
                "expiry_date": batch["expiry_date"] if batch else None}

    def _find_batch(self, product_id, batch_id=None):
        rows = self.db.query("SELECT id FROM product WHERE id = ? AND archived = 0", (product_id,))
        if not rows:
            raise ValidationError({"product": "Product not found."})
        if batch_id is not None:
            found = self.db.query("SELECT id, expiry_date FROM stock_batch WHERE id = ? AND product_id = ?",
                                  (batch_id, product_id))
            if not found:
                raise ValidationError({"batch": "Batch not found for this product."})
            return found[0]
        batches = self.db.query("SELECT id, expiry_date FROM stock_batch WHERE product_id = ? ORDER BY id",
                                (product_id,))
        if len(batches) > 1:
            return None            # caller must name a batch before an expiry date can be edited
        return batches[0] if batches else None

    def update_product(self, user, product_id, name=None, expiry=None, threshold=None, batch_id=None):
        """FID-3. None = leave that field unchanged; expiry="" clears the expiry date.
        Returns True if something was saved, False if nothing changed.
        Raises PermissionDenied, ValidationError({field: message}) or DuplicateProductError."""
        self.login.require(user, "update_product")                       # SR-3.1
        errors = {}
        old = self.db.query("SELECT name, low_stock_level FROM product WHERE id = ? AND archived = 0",
                            (product_id,))
        if not old:
            raise ValidationError({"product": "Product not found."})
        old_name, old_threshold = old[0]["name"], old[0]["low_stock_level"]

        new_name = old_name                                              # SR-3.3 validation
        if name is not None:
            new_name = str(name).strip()
            if not new_name:
                errors["name"] = "Product name is required."
        new_threshold = old_threshold
        if threshold is not None:
            new_threshold = _whole_number(threshold)
            if new_threshold is None:
                errors["threshold"] = "Low-stock level must be a whole number of 0 or more."

        batch, new_expiry, old_expiry = None, None, None
        if expiry is not None:
            try:
                batch = self._find_batch(product_id, batch_id)
            except ValidationError as exc:
                errors.update(exc.errors)
            else:
                if batch is None:
                    errors["batch"] = "This product has several batches: choose which batch to change."
                else:
                    old_expiry = batch["expiry_date"]
                    text = str(expiry).strip()
                    if text == "":
                        new_expiry = None                                # blank clears the date
                    else:
                        try:
                            new_expiry = datetime.strptime(text, "%Y-%m-%d").date().isoformat()
                        except ValueError:
                            errors["expiry"] = "Enter a valid date (YYYY-MM-DD)."
        if errors:
            raise ValidationError(errors)

        if new_name != old_name and self.db.query(                       # names stay unique
                "SELECT 1 FROM product WHERE name = ? AND id != ?", (new_name, product_id)):
            raise DuplicateProductError(f"'{new_name}' already exists.")

        changes = []
        if new_name != old_name:
            changes.append(f"name '{old_name}' -> '{new_name}'")
        if new_threshold != old_threshold:
            changes.append(f"low-stock level {old_threshold} -> {new_threshold}")
        if batch is not None and new_expiry != old_expiry:
            changes.append(f"expiry {old_expiry or 'none'} -> {new_expiry or 'none'}")
        if not changes:
            return False

        now = datetime.now().isoformat(timespec="seconds")
        with self.db.transaction() as c:                                 # SR-3.4, SAF-2
            c.execute("UPDATE product SET name = ?, low_stock_level = ? WHERE id = ?",
                      (new_name, new_threshold, product_id))
            if batch is not None:
                c.execute("UPDATE stock_batch SET expiry_date = ? WHERE id = ?", (new_expiry, batch["id"]))
            c.execute("INSERT INTO audit_log(action, detail, performed_by, date_time)"   # SR-3.5
                      " VALUES ('update_product', ?, ?, ?)",
                      (f"{old_name}: " + "; ".join(changes), user.username, now))
        return True

    # ---------- FID-2 Remove Product ----------
    def removal_summary(self, user, product_id):
        """What the confirmation prompt shows before a removal: product name and current quantity
        (SR-2.3). Raises PermissionDenied (SR-2.1) or ValidationError if the product no longer exists (SR-2.2)."""
        self.login.require(user, "remove_product")
        row = self.db.query("SELECT id, name FROM product WHERE id = ? AND archived = 0", (product_id,))
        if not row:
            raise ValidationError({"product": "Product not found. It may already have been removed."})
        qty = self.db.query("SELECT COALESCE(SUM(qty_in_stock), 0) AS n FROM stock_batch WHERE product_id = ?",
                            (product_id,))[0]["n"]
        return {"product_id": row[0]["id"], "name": row[0]["name"], "quantity": qty}

    def remove_product(self, user, product_id, reason):
        """Call this only after the user has confirmed in the prompt (SR-2.3). The product is archived, so it
        disappears from the inventory, search and alerts, while its stock history and audit records stay
        (SR-2.4). Returns the product name. Nothing changes if anything fails (SR-2.5)."""
        info = self.removal_summary(user, product_id)                    # SR-2.1, SR-2.2
        reason = (reason or "").strip()
        if not reason:
            raise ValidationError({"reason": "Enter a reason for removing the product."})
        if len(reason) > 200:
            raise ValidationError({"reason": "Reason must be 200 characters or fewer."})
        now = datetime.now().isoformat(timespec="seconds")
        with self.db.transaction() as c:                                 # SR-2.4, SAF-2
            # the name is freed so the same name can be added again later; the original is kept in the log
            c.execute("UPDATE product SET archived = 1, name = ? WHERE id = ?",
                      (f"{info['name']} [removed #{product_id}]", product_id))
            c.execute("INSERT INTO audit_log(action, detail, performed_by, date_time)"
                      " VALUES ('remove_product', ?, ?, ?)",
                      (f"{info['name']} ({info['quantity']} In Stock): {reason}", user.username, now))
        return info["name"]

    # ---------- FID-7 Search ----------
    def search_products(self, user, name="", min_quantity=None, max_quantity=None, status=""):
        """Find stock rows by product name (part of the name, any case), In Stock quantity range and/or
        status label; any combination. Search text is only ever compared as text, never run as SQL (SEC-6).
        Returns the same row dicts as list_batches(). An empty list means nothing matched (UC 07 A3).
        Raises ValidationError if nothing was entered or an input is invalid."""
        self.login.require(user, "view_products")
        errors = {}
        name = (name or "").strip()
        status = (status or "").strip()
        lo = hi = None
        if str(min_quantity if min_quantity is not None else "").strip() != "":
            lo = _whole_number(min_quantity)
            if lo is None:
                errors["min_quantity"] = "Enter a whole number of 0 or more."
        if str(max_quantity if max_quantity is not None else "").strip() != "":
            hi = _whole_number(max_quantity)
            if hi is None:
                errors["max_quantity"] = "Enter a whole number of 0 or more."
        if status and status not in STATUS_LABELS:
            errors["status"] = "Choose one of: " + ", ".join(STATUS_LABELS) + "."
        if not errors and not (name or status or lo is not None or hi is not None):
            errors["search"] = "Enter a product name, a quantity or a status to search."
        if not errors and lo is not None and hi is not None and lo > hi:
            errors["min_quantity"] = "The minimum cannot be greater than the maximum."
        if errors:
            raise ValidationError(errors)

        rows = self.list_batches(user)
        totals = {}
        for r in rows:
            totals[r["product_id"]] = totals.get(r["product_id"], 0) + r["qty_in_stock"]
        found = []
        for r in rows:
            if name and name.lower() not in r["name"].lower():
                continue
            if lo is not None and r["qty_in_stock"] < lo:
                continue
            if hi is not None and r["qty_in_stock"] > hi:
                continue
            if status == "Low Stock":
                total = totals[r["product_id"]]
                if not (total > 0 and self.rules.is_low_stock(total, r["threshold"])):
                    continue
            elif status and r["status"] != status:
                continue
            found.append(r)
        return found
