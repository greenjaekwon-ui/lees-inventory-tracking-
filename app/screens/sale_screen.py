"""SaleScreen (FID-9): record a sale of one product. The cashier enters a sale reference once per sale."""
import tkinter as tk
from tkinter import messagebox, ttk

from .ui_helpers import report_error


class SaleScreen(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.product_ids = {}
        self.product, self.quantity, self.sale_ref = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(self, text="Record a sale (FID-9)", font=("Segoe UI", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Label(self, text="Product").grid(row=1, column=0, sticky="w", pady=3)
        self.product_box = ttk.Combobox(self, textvariable=self.product, state="readonly", width=34)
        self.product_box.grid(row=1, column=1, pady=3, padx=(8, 0))
        ttk.Label(self, text="Quantity sold").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(self, textvariable=self.quantity, width=36).grid(row=2, column=1, pady=3, padx=(8, 0))
        ttk.Label(self, text="Sale reference (unique)").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Entry(self, textvariable=self.sale_ref, width=36).grid(row=3, column=1, pady=3, padx=(8, 0))
        ttk.Button(self, text="Record sale", command=self.on_record).grid(row=4, column=0, columnspan=2, pady=12)

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
        try:
            remaining = self.app.stock.record_sale(self.app.user, self.product_ids.get(name),
                                                   self.quantity.get(), self.sale_ref.get())
        except Exception as exc:
            report_error(exc)
            return
        messagebox.showinfo("Saved", f"Sale recorded: {self.quantity.get().strip()} x {name}.\n"
                                     f"Remaining In Stock: {remaining}")
        self.quantity.set("")
        self.sale_ref.set("")
        self.refresh()
