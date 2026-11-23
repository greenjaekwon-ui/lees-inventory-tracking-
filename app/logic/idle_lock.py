"""IdleLock (SEC-3): signs the user out after 15 minutes with no keyboard or mouse activity.
Uses tkinter's after() like ExpiryTimer, so it stays on one thread and is easy to test with a fake root."""

IDLE_MS = 15 * 60 * 1000


class IdleLock:
    def __init__(self, root, on_lock, timeout_ms=IDLE_MS):
        self.root, self.on_lock, self.timeout_ms = root, on_lock, timeout_ms
        self._job = None
        self._running = False

    def start(self):
        self._running = True
        self.reset()

    def reset(self, _event=None):
        """Call on every key press, click or mouse move: restarts the countdown (only while signed in)."""
        if not self._running:
            return
        self._cancel()
        self._job = self.root.after(self.timeout_ms, self._fire)

    def stop(self):
        self._running = False
        self._cancel()

    def _cancel(self):
        if self._job is not None:
            self.root.after_cancel(self._job)
            self._job = None

    def _fire(self):
        self._job = None
        self.on_lock()
