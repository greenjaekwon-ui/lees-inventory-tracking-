"""StockScreen (FID-4): record stock received or a count correction."""
import tkinter as tk
from tkinter import messagebox, ttk

from app.logic.models import ChangeType
from .ui_helpers import report_error

TYPES = (ChangeType.STOCK_RECEIVED.value, ChangeType.COUNT_CORRECTION.value)


class StockScreen(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.product_ids = {}
        self.product, self.kind, self.quantity = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.reason, self.expiry = tk.StringVar(), tk.StringVar()
        ttk.Label(self, text="Stock change (FID-4)", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Label(self, text="Product").grid(row=1, column=0, sticky="w", pady=3)
        self.product_box = ttk.Combobox(self, textvariable=self.product, state="readonly", width=34)
        self.product_box.grid(row=1, column=1, pady=3, padx=(8, 0))
        ttk.Label(self, text="Change type").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Combobox(self, textvariable=self.kind, values=TYPES, state="readonly", width=34).grid(
            row=2, column=1, pady=3, padx=(8, 0))
        ttk.Label(self, text="Quantity (correction: e.g. -5 or 5)").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Entry(self, textvariable=self.quantity, width=36).grid(row=3, column=1, pady=3, padx=(8, 0))
        ttk.Label(self, text="Reason").grid(row=4, column=0, sticky="w", pady=3)
        ttk.Entry(self, textvariable=self.reason, width=36).grid(row=4, column=1, pady=3, padx=(8, 0))
        ttk.Label(self, text="Expiry date for received stock (YYYY-MM-DD, optional)").grid(row=5, column=0, sticky="w", pady=3)
        ttk.Entry(self, textvariable=self.expiry, width=36).grid(row=5, column=1, pady=3, padx=(8, 0))
        ttk.Button(self, text="Save change", command=self.on_save).grid(row=6, column=0, columnspan=2, pady=12)

    def refresh(self):
        try:
            products = self.app.products.list_products(self.app.user)
        except Exception as exc:
            report_error(exc)
            return
        self.product_ids = {name: pid for pid, name in products}
        self.product_box["values"] = list(self.product_ids)

    def on_save(self):
        if not messagebox.askyesno("Confirm", "Save this stock change?"):
            return                                       # cancelled: nothing changed or logged
        try:
            level = self.app.stock.change_stock(self.app.user, self.product_ids.get(self.product.get()),
                                                self.kind.get(), self.quantity.get(), self.reason.get(),
                                                expiry=self.expiry.get())
        except Exception as exc:
            report_error(exc)
            return
        messagebox.showinfo("Saved", f"Stock updated. In Stock now: {level}")
        for var in (self.quantity, self.reason, self.expiry):
            var.set("")
        self.refresh()
