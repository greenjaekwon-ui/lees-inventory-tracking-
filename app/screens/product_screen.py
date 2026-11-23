"""ProductScreen (SDS 3.1). Add form = FID-1 (Jaekwon). Update form = FID-3 (Brandon)."""
import tkinter as tk
from tkinter import messagebox, ttk

from .ui_helpers import fill_table, report_error

COLUMNS = (("name", "Product", 170), ("batch_id", "Batch", 50), ("expiry_date", "Expiry", 90),
           ("status", "Status", 75), ("qty_in_stock", "In Stock", 70), ("qty_sold", "Sold", 55), ("qty_damaged", "Damaged", 70),
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
        self.rows = []                                   # row dicts, same order as the table

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
            self.rows = self.app.products.list_batches(self.app.user)
            fill_table(self.tree, self.rows, [c[0] for c in COLUMNS])
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
        """FID-3: open the update form for the selected row (SR-3.1, SR-3.2)."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Update product", "Select a row in the table first.")
            return
        row = self.rows[self.tree.index(selected[0])]
        try:
            details = self.app.products.get_product_details(self.app.user, row["product_id"], row["batch_id"])
        except Exception as exc:
            report_error(exc)                            # e.g. access denied
            return
        EditDialog(self, details)


class EditDialog(tk.Toplevel):
    """Update form: Save asks for confirmation; Cancel or 'No' leaves the product unchanged (SR-3.4)."""

    def __init__(self, screen, details):
        super().__init__(screen)
        self.screen, self.details = screen, details
        self.title("Update product")
        self.resizable(False, False)
        self.name = tk.StringVar(value=details["name"])
        self.threshold = tk.StringVar(value=str(details["threshold"]))
        self.expiry = tk.StringVar(value=details["expiry_date"] or "")     # blank if no expiry date
        body = ttk.Frame(self, padding=14)
        body.pack()
        for i, (label, var) in enumerate((("Name", self.name), ("Low-stock level", self.threshold),
                                          ("Expiry date (YYYY-MM-DD, blank = none)", self.expiry))):
            ttk.Label(body, text=label).grid(row=i, column=0, sticky="w", pady=3)
            ttk.Entry(body, textvariable=var, width=26).grid(row=i, column=1, padx=(8, 0), pady=3)
        buttons = ttk.Frame(body)
        buttons.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(buttons, text="Save", command=self.on_save).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.transient(screen)
        self.grab_set()

    def on_save(self):
        if not messagebox.askyesno("Confirm", "Save these changes?", parent=self):
            return                                       # cancelled at the confirmation step: nothing saved
        d = self.details
        try:
            saved = self.screen.app.products.update_product(
                self.screen.app.user, d["product_id"], name=self.name.get(), threshold=self.threshold.get(),
                expiry=self.expiry.get() if d["batch_id"] is not None else None, batch_id=d["batch_id"])
        except Exception as exc:
            report_error(exc)                            # failed save: no success message, form stays open
            return
        messagebox.showinfo("Saved", "Product updated." if saved else "No changes were made.", parent=self)
        self.destroy()
        self.screen.refresh()
