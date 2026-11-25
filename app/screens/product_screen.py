"""ProductScreen (SDS 3.1). Add form = FID-1, update = FID-3, remove = FID-2, search = FID-7."""
import tkinter as tk
from tkinter import messagebox, ttk

from app.logic.product_manager import STATUS_LABELS
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
        remove = ttk.LabelFrame(self, text="Remove product (FID-2)", padding=10)
        remove.grid(row=2, column=0, sticky="nw", padx=(0, 12), pady=(12, 0))
        ttk.Label(remove, text="Select a row in the table, then:").pack(anchor="w")
        ttk.Button(remove, text="Remove selected...", command=self.on_remove).pack(anchor="w", pady=4)
        self.rows = []                                   # row dicts, same order as the table

        right = ttk.Frame(self)
        right.grid(row=0, column=1, rowspan=3, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.s_name, self.s_min, self.s_max, self.s_status = (tk.StringVar() for _ in range(4))
        bar = ttk.LabelFrame(right, text="Search (FID-7)", padding=6)
        bar.pack(fill="x", pady=(0, 6))
        ttk.Label(bar, text="Name").grid(row=0, column=0)
        ttk.Entry(bar, textvariable=self.s_name, width=16).grid(row=0, column=1, padx=4)
        ttk.Label(bar, text="In Stock from").grid(row=0, column=2)
        ttk.Entry(bar, textvariable=self.s_min, width=6).grid(row=0, column=3, padx=4)
        ttk.Label(bar, text="to").grid(row=0, column=4)
        ttk.Entry(bar, textvariable=self.s_max, width=6).grid(row=0, column=5, padx=4)
        ttk.Label(bar, text="Status").grid(row=0, column=6)
        ttk.Combobox(bar, textvariable=self.s_status, values=[""] + list(STATUS_LABELS), state="readonly",
                     width=12).grid(row=0, column=7, padx=4)
        ttk.Button(bar, text="Search", command=self.on_search).grid(row=0, column=8, padx=4)
        ttk.Button(bar, text="Show all", command=self.on_show_all).grid(row=0, column=9)
        self.message = ttk.Label(right, text="")
        self.message.pack(anchor="w")
        table = ttk.Frame(right)
        table.pack(fill="both", expand=True)
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
            self.message.config(text="")
        except Exception as exc:
            report_error(exc)

    def on_show_all(self):
        for var in (self.s_name, self.s_min, self.s_max, self.s_status):
            var.set("")
        self.refresh()

    def on_search(self):
        """FID-7: show only the matching rows, or a message when nothing matches."""
        try:
            self.rows = self.app.products.search_products(self.app.user, self.s_name.get(), self.s_min.get(),
                                                          self.s_max.get(), self.s_status.get())
        except Exception as exc:
            report_error(exc)
            return
        fill_table(self.tree, self.rows, [c[0] for c in COLUMNS])
        self.message.config(text=f"{len(self.rows)} matching row(s)." if self.rows else
                            "No matching product was found.")

    def on_remove(self):
        """FID-2: ask for confirmation and a reason, then remove (archive) the selected product."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Remove product", "Select a row in the table first.")
            return
        row = self.rows[self.tree.index(selected[0])]
        try:
            info = self.app.products.removal_summary(self.app.user, row["product_id"])
        except Exception as exc:
            report_error(exc)
            self.refresh()
            return
        RemoveDialog(self, info)

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


class RemoveDialog(tk.Toplevel):
    """Shows the product name and quantity, asks for a reason; nothing is removed until Remove is pressed
    and confirmed (SR-2.3). Cancel leaves the product unchanged (SR-2.5)."""

    def __init__(self, screen, info):
        super().__init__(screen)
        self.screen, self.info = screen, info
        self.title("Remove product")
        self.resizable(False, False)
        self.reason = tk.StringVar()
        body = ttk.Frame(self, padding=14)
        body.pack()
        ttk.Label(body, text=f"Remove \"{info['name']}\"?\nCurrent In Stock quantity: {info['quantity']}").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(body, text="Reason").grid(row=1, column=0, sticky="w")
        ttk.Entry(body, textvariable=self.reason, width=30).grid(row=1, column=1, padx=(8, 0))
        buttons = ttk.Frame(body)
        buttons.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(buttons, text="Remove", command=self.on_remove).pack(side="left", padx=4)
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="left", padx=4)
        self.transient(screen)
        self.grab_set()

    def on_remove(self):
        if not self.reason.get().strip():
            messagebox.showerror("Please correct these fields", "reason: Enter a reason for removing the product.", parent=self)
            return
        if not messagebox.askyesno("Confirm", f"Really remove {self.info['name']}?", parent=self):
            return
        try:
            name = self.screen.app.products.remove_product(self.screen.app.user, self.info["product_id"], self.reason.get())
        except Exception as exc:
            report_error(exc)                            # failed removal: product stays, no success message
            return
        messagebox.showinfo("Removed", f"{name} was removed from the inventory.", parent=self)
        self.destroy()
        self.screen.refresh()
