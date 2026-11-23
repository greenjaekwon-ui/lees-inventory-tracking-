"""ProductScreen (SDS 3.1). Add form = FID-1 (Jaekwon). Update form = FID-3 (Brandon, TODO)."""
import tkinter as tk
from tkinter import messagebox, ttk

from .ui_helpers import fill_table, report_error

COLUMNS = (("name", "Product", 170), ("batch_id", "Batch", 50), ("expiry_date", "Expiry", 90),
           ("qty_in_stock", "In Stock", 70), ("qty_sold", "Sold", 55), ("qty_damaged", "Damaged", 70),
           ("qty_expired", "Expired", 65), ("threshold", "Low-stock level", 100))


class ProductScreen(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        self.name, self.quantity = tk.StringVar(), tk.StringVar()
        self.expiry, self.threshold = tk.StringVar(), tk.StringVar(value="0")

        form = ttk.LabelFrame(self, text="Add product (FID-1)", padding=10)
        form.grid(row=0, column=0, sticky="nw", padx=(0, 12))
        fields = (("Name", self.name), ("Quantity", self.quantity),
                  ("Expiry date (YYYY-MM-DD, optional)", self.expiry), ("Low-stock level", self.threshold))
        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", pady=2)
            ttk.Entry(form, textvariable=var, width=22).grid(row=i, column=1, padx=(8, 0), pady=2)
        ttk.Button(form, text="Add product", command=self.on_add).grid(row=len(fields), column=0, columnspan=2, pady=(8, 0))

        edit = ttk.LabelFrame(self, text="Update product (FID-3)", padding=10)
        edit.grid(row=1, column=0, sticky="nw", padx=(0, 12), pady=(12, 0))
        ttk.Label(edit, text="Select a row in the table, then:").pack(anchor="w")
        ttk.Button(edit, text="Edit selected...", command=self.on_edit).pack(anchor="w", pady=4)
        # TODO (Brandon): replace on_edit with a form that calls self.app.products.update_product(...)

        table = ttk.Frame(self)
        table.grid(row=0, column=1, rowspan=2, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        self.tree = ttk.Treeview(table, columns=[c[0] for c in COLUMNS], show="headings", height=20)
        for key, title, width in COLUMNS:
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

    def refresh(self):
        try:
            fill_table(self.tree, self.app.products.list_batches(self.app.user), [c[0] for c in COLUMNS])
        except Exception as exc:
            report_error(exc)

    def on_add(self):
        try:
            self.app.products.add_product(self.app.user, self.name.get(), self.quantity.get(),
                                          self.expiry.get(), self.threshold.get())
        except Exception as exc:
            report_error(exc)
            return
        messagebox.showinfo("Saved", "Product added.")
        for var in (self.name, self.quantity, self.expiry):
            var.set("")
        self.threshold.set("0")
        self.refresh()

    def on_edit(self):
        # TODO (Brandon) FID-3: open an edit form for the selected product.
        try:
            self.app.products.update_product(self.app.user, None)
        except Exception as exc:
            report_error(exc)
