"""BusinessRules (the SDS 'Rules' component): the ONLY place the store's rules live (QA-3).
Every method takes `today` so tests can pass boundary dates."""

WARNING_DAYS = 30


class BusinessRules:
    warning_days = WARNING_DAYS

    @staticmethod
    def is_past_expiry(expiry, today):
        """Expired only the day AFTER the expiry date (FID-11 SR-11.2)."""
        return expiry is not None and expiry < today

    @classmethod
    def is_nearing_expiry(cls, expiry, today):
        """Inclusive window of 0 to 30 days from today (UC 06)."""
        return expiry is not None and 0 <= (expiry - today).days <= cls.warning_days

    @staticmethod
    def is_low_stock(in_stock_qty, threshold):
        """Equal to or below the threshold (FID-5). A threshold of 0 means no threshold is set, so no alert."""
        return bool(threshold) and in_stock_qty <= threshold

    @classmethod
    def can_sell(cls, in_stock_qty, qty, expiry, today):
        return 0 < qty <= in_stock_qty and not cls.is_past_expiry(expiry, today)

    @classmethod
    def is_valid_new_expiry(cls, expiry, today):
        """FID-1 SR-1.3: today's date is accepted, earlier dates are rejected."""
        return expiry >= today

    @staticmethod
    def batch_status(in_stock_qty, last_to_status):
        """Status shown for a batch: In Stock while usable units remain; otherwise the status its units
        last moved to (Damaged, Expired or Sold); a batch that never had units shows 'Out of Stock'
        (a flag, not one of the four statuses - FID-8 TS-8.1B)."""
        if in_stock_qty > 0:
            return "In Stock"
        if last_to_status in ("Damaged", "Expired", "Sold"):
            return last_to_status
        return "Out of Stock"
