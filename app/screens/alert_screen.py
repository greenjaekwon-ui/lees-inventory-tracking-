"""AlertScreen (SDS 3.1). Low stock = FID-5 (Ricardo). Nearing expiry = FID-6 (Tevin).
'Run expiry check now' triggers FID-11 (Janae) so you can see it work without waiting 24 hours."""
import tkinter as tk
from tkinter import messagebox, ttk

from .ui_helpers import fill_table, report_error


class AlertScreen(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Button(bar, text="Refresh alerts", command=self.refresh).pack(side="left")
        ttk.Button(bar, text="Run expiry check now (FID-11)", command=self.on_expiry_check).pack(side="left", padx=8)

        self.low = self._table("Low-stock alerts (FID-5)",
                               (("name", "Product", 220), ("in_stock", "In Stock", 90), ("threshold", "Low-stock level", 120)))
        self.expiring = self._table("Nearing-expiry notifications (FID-6)",
                                    (("name", "Product", 220), ("quantity", "Quantity", 90), ("expiry_date", "Expiry date", 120)))

    def _table(self, title, columns):
        box = ttk.LabelFrame(self, text=title, padding=6)
        box.pack(fill="both", expand=True, pady=(0, 8))
        tree = ttk.Treeview(box, columns=[c[0] for c in columns], show="headings", height=8)
        for key, heading, width in columns:
            tree.heading(key, text=heading)
            tree.column(key, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        tree.keys = [c[0] for c in columns]
        return tree

    def _load(self, tree, fetch, placeholder):
        try:
            fill_table(tree, fetch(self.app.user), tree.keys)
        except NotImplementedError:
            tree.delete(*tree.get_children())
            tree.insert("", "end", values=[placeholder] + [""] * (len(tree.keys) - 1))
        except Exception as exc:
            report_error(exc)

    def refresh(self):
        self._load(self.low, self.app.alerts.low_stock_alerts, "(FID-5 not built yet - Ricardo)")
        self._load(self.expiring, self.app.alerts.nearing_expiry_notifications, "(FID-6 not built yet - Tevin)")

    def on_expiry_check(self):
        try:
            self.app.login.require(self.app.user, "run_expiry_check")
        except Exception as exc:
            report_error(exc)
            return
        moved = self.app.timer.run_now()
        messagebox.showinfo("Expiry check", f"Expiry check finished. Units moved to Expired: {moved}")
        self.refresh()
