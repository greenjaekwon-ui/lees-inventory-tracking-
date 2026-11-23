"""ProductManager. FID-1 add (Jaekwon, DONE), FID-3 update (Brandon, TODO)."""
import re
from datetime import date, datetime

from .errors import DuplicateProductError, ValidationError
from .rules import BusinessRules


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
        """One dict per stock batch, for the product table."""
        self.login.require(user, "view_products")
        rows = self.db.query(
            "SELECT p.id AS product_id, p.name, p.low_stock_level AS threshold, b.id AS batch_id,"
            " b.expiry_date, b.qty_in_stock, b.qty_sold, b.qty_damaged, b.qty_expired"
            " FROM product p JOIN stock_batch b ON b.product_id = p.id"
            " WHERE p.archived = 0 ORDER BY p.name, b.expiry_date")
        return [dict(r) for r in rows]

    def list_products(self, user):
        """(id, name) pairs for drop-down lists."""
        self.login.require(user, "view_products")
        return [(r["id"], r["name"]) for r in
                self.db.query("SELECT id, name FROM product WHERE archived = 0 ORDER BY name")]

    # ---------- FID-3 Update Product (Brandon) ----------
    def update_product(self, user, product_id, name=None, expiry=None, threshold=None, batch_id=None):
        """TODO (Brandon) FID-3, SR-3.1 to SR-3.5: check permission ('update_product'), validate
        (empty name, invalid expiry date, threshold not a whole number), keep names unique,
        save in ONE transaction, write an audit_log row with old and new values (SR-3.5).
        Copy the pattern of add_product above."""
        raise NotImplementedError("FID-3 Update Product - owner: Brandon")
