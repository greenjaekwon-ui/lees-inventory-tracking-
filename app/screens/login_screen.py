"""LoginScreen (SDS 3.1): collects credentials and passes them to LoginManager."""
import tkinter as tk
from tkinter import ttk

from app.logic.errors import AuthError


class LoginScreen(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=40)
        self.app = app
        ttk.Label(self, text="Lee's Wholesale Inventory Tracking System", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 20))
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        ttk.Label(self, text="Username").grid(row=1, column=0, sticky="e", padx=5, pady=4)
        user_entry = ttk.Entry(self, textvariable=self.username, width=28)
        user_entry.grid(row=1, column=1, pady=4)
        ttk.Label(self, text="Password").grid(row=2, column=0, sticky="e", padx=5, pady=4)
        pass_entry = ttk.Entry(self, textvariable=self.password, show="*", width=28)
        pass_entry.grid(row=2, column=1, pady=4)
        self.message = ttk.Label(self, text="", foreground="#b00020")
        self.message.grid(row=3, column=0, columnspan=2, pady=4)
        ttk.Button(self, text="Sign in", command=self.on_sign_in).grid(row=4, column=0, columnspan=2, pady=8)
        pass_entry.bind("<Return>", lambda _e: self.on_sign_in())
        user_entry.focus_set()

    def on_sign_in(self):
        try:
            user = self.app.login.authenticate(self.username.get().strip(), self.password.get())
        except AuthError as exc:
            self.message.config(text=str(exc))
            self.password.set("")
            return
        self.app.show_main(user)
