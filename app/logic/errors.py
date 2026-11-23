class PermissionDenied(Exception):
    """The signed-in user's role may not do this action (SEC-1)."""

class AuthError(Exception):
    """Wrong username or password. Same message for either (SEC-3)."""

class ValidationError(Exception):
    """Carries {field: message} so a screen can show each field to correct."""
    def __init__(self, errors):
        super().__init__(errors)
        self.errors = errors

class DuplicateProductError(Exception):
    """The product name already exists (FID-1 SR-1.4)."""
