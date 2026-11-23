"""Shared screen helpers. Screens only collect input, call ONE manager, and show the result."""
from tkinter import messagebox

from app.logic.errors import DuplicateProductError, PermissionDenied, ValidationError


def report_error(exc):
    """Show a friendly message for the expected errors; re-raise real bugs so they show in the console."""
    if isinstance(exc, ValidationError):
        lines = [f"{field}: {message}" for field, message in exc.errors.items()]
        messagebox.showerror("Please correct these fields", "\n".join(lines))
    elif isinstance(exc, DuplicateProductError):
        messagebox.showerror("Duplicate product", str(exc))
    elif isinstance(exc, PermissionDenied):
        messagebox.showerror("Access denied", "You do not have permission to do that.")
    elif isinstance(exc, NotImplementedError):
        messagebox.showinfo("Not built yet", str(exc))
    else:
        raise exc


def fill_table(tree, rows, keys):
    """Replace the rows of a ttk.Treeview. `rows` are dicts, `keys` the column keys in order."""
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", "end", values=[("" if row.get(k) is None else row.get(k)) for k in keys])
