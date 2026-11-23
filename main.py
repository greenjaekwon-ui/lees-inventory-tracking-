"""Lee's Wholesale Inventory Tracking System. Run:  python main.py
First time? Add sample data:  python -m app.data.seed --demo
Login (demo): manager / manager123   (also owner, warehouse, cashier - see app/data/seed.py)"""
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from app.data.database import Database
from app.data.seed import ensure_seed
from app.logic.alert_manager import AlertManager
from app.logic.expiry_timer import ExpiryTimer
from app.logic.idle_lock import IdleLock
from app.logic.login_manager import LoginManager
from app.logic.product_manager import ProductManager
from app.logic.stock_manager import StockManager
from app.screens.alert_screen import AlertScreen
from app.screens.damage_screen import DamageScreen
from app.screens.login_screen import LoginScreen
from app.screens.product_screen import ProductScreen

DB_PATH = Path(__file__).with_name("lees_inventory.db")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Lee's Wholesale Inventory Tracking System")
        self.geometry("1100x640")                       # fits the client's 1366 x 768 screen
        self.db = Database(str(DB_PATH))
        ensure_seed(self.db)
        self.login = LoginManager(self.db)
        self.products = ProductManager(self.db, self.login)
        self.stock = StockManager(self.db, self.login)
        self.alerts = AlertManager(self.db, self.login)
        self.timer = ExpiryTimer(self, self.stock)
        self.idle = IdleLock(self, self.auto_sign_out)       # SEC-3: 15 minutes
        self.user = None
        self.body = None
        for event in ("<Key>", "<Button>", "<Motion>"):      # any activity restarts the idle countdown
            self.bind_all(event, self.idle.reset, add="+")
        self.screens = []
        self.show_login()

    def _swap_body(self):
        if self.body is not None:
            self.body.destroy()
        self.body = ttk.Frame(self)
        self.body.pack(fill="both", expand=True)
        return self.body

    def show_login(self):
        self.timer.stop()
        self.idle.stop()
        self.user = None
        self.screens = []
        LoginScreen(self._swap_body(), self).pack(expand=True)

    def show_main(self, user):
        self.user = user
        body = self._swap_body()
        top = ttk.Frame(body)
        top.pack(fill="x", padx=10, pady=6)
        ttk.Label(top, text=f"Signed in as {user.username} ({user.role.value})").pack(side="left")
        ttk.Button(top, text="Sign out", command=self.sign_out).pack(side="right")

        notebook = ttk.Notebook(body)
        notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # each role only gets the tabs it may use (the managers still check permission on every call, SEC-1)
        wanted = (("Products", ProductScreen, "view_products"),
                  ("Record damage", DamageScreen, "record_damage"),
                  ("Alerts", AlertScreen, "view_alerts"))
        self.screens = []
        for title, screen_class, permission in wanted:
            if user.has_permission(permission):
                screen = screen_class(notebook, self)
                notebook.add(screen, text=title)
                self.screens.append(screen)
        notebook.bind("<<NotebookTabChanged>>", lambda _e: self.screens[notebook.index("current")].refresh())
        self.timer.start()                              # expiry check at start-up, then every 24 hours
        self.idle.start()
        if self.screens:
            self.screens[0].refresh()

    def sign_out(self):
        self.show_login()

    def auto_sign_out(self):
        """Called by IdleLock after 15 minutes of no activity (SEC-3)."""
        self.show_login()
        messagebox.showinfo("Signed out", "You were signed out after 15 minutes without activity.")


if __name__ == "__main__":
    App().mainloop()
