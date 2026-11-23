"""DamageScreen (SDS 3.1) for FID-10 (D'mitri)."""
import tkinter as tk
from tkinter import messagebox, ttk

from app.logic.models import DamageReason
from .ui_helpers import report_error


class DamageScreen(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.product_ids = {}
        self.product, self.quantity = tk.StringVar(), tk.StringVar()
        self.reason, self.note = tk.StringVar(), tk.StringVar()

        ttk.Label(self, text="Record damaged product (FID-10)", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Label(self, text="Product").grid(row=1, column=0, sticky="w", pady=3)
        self.product_box = ttk.Combobox(self, textvariable=self.product, state="readonly", width=34)
        self.product_box.grid(row=1, column=1, pady=3, padx=(8, 0))
        ttk.Label(self, text="Damaged quantity").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(self, textvariable=self.quantity, width=36).grid(row=2, column=1, pady=3, padx=(8, 0))
        ttk.Label(self, text="Reason").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Combobox(self, textvariable=self.reason, state="readonly", width=34,
                     values=[r.value for r in DamageReason]).grid(row=3, column=1, pady=3, padx=(8, 0))
        ttk.Label(self, text="Note (optional, up to 200 characters)").grid(row=4, column=0, sticky="w", pady=3)
        ttk.Entry(self, textvariable=self.note, width=36).grid(row=4, column=1, pady=3, padx=(8, 0))
        ttk.Button(self, text="Record damage", command=self.on_record).grid(row=5, column=0, columnspan=2, pady=12)

    def refresh(self):
        try:
            products = self.app.products.list_products(self.app.user)
        except Exception as exc:
            report_error(exc)
            return
        self.product_ids = {name: pid for pid, name in products}
        self.product_box["values"] = list(self.product_ids)

    def on_record(self):
        name = self.product.get()
        product_id = self.product_ids.get(name)                    # None if nothing selected
        quantity = self.quantity.get().strip()
        try:
            remaining = self.app.stock.record_damage(self.app.user, product_id, quantity,
                                                     self.reason.get(), self.note.get())
        except Exception as exc:
            report_error(exc)                                      # the entered data stays on the form
            return
        messagebox.showinfo("Saved", f"Damage recorded for {name}: {quantity} unit(s).\n"
                                     f"Remaining In Stock: {remaining}")
        self.quantity.set("")
        self.note.set("")
        self.refresh()
