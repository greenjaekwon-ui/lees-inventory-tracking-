"""LoginManager (SEC-1, SEC-2, SEC-3). Every other manager calls require() first.
TODO (Janae): 15-minute idle lock (SEC-3) in main.py using App.sign_out()."""
import hashlib
import hmac
import os
from datetime import datetime

from .errors import AuthError, PermissionDenied
from .models import Role, User

_ITERATIONS = 200_000


def hash_password(password, salt=None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return salt.hex() + "$" + digest.hex()


def verify_password(password, stored):
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), _ITERATIONS)
    return hmac.compare_digest(digest.hex(), digest_hex)


class LoginManager:
    def __init__(self, db):
        self.db = db

    def create_user(self, username, password, role):
        with self.db.transaction() as c:
            c.execute("INSERT INTO user(username, password_hash, role) VALUES (?,?,?)",
                      (username, hash_password(password), role.name))

    def authenticate(self, username, password):
        """Returns a User, or raises AuthError (same message whichever detail was wrong)."""
        rows = self.db.query("SELECT * FROM user WHERE username = ? AND active = 1", (username,))
        if not rows or not verify_password(password, rows[0]["password_hash"]):
            raise AuthError("Incorrect username or password.")
        row = rows[0]
        return User(row["id"], row["username"], Role[row["role"]])

    def require(self, user, action):
        """Call this at the top of every manager method (SEC-1)."""
        if user is None or not user.has_permission(action):
            raise PermissionDenied(f"'{action}' is not permitted for this user.")
