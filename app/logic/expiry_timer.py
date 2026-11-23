"""ExpiryTimer: runs the expiry check when the app starts and every 24 hours (SDS 2.3.1).
Uses tkinter's after() so everything stays on one thread (sqlite3 needs that)."""

ONE_DAY_MS = 24 * 60 * 60 * 1000


class ExpiryTimer:
    def __init__(self, root, stock_manager, interval_ms=ONE_DAY_MS):
        self.root, self.stock, self.interval_ms = root, stock_manager, interval_ms
        self._job = None

    def start(self):
        self.run_now()
        self._job = self.root.after(self.interval_ms, self.start)

    def stop(self):
        if self._job is not None:
            self.root.after_cancel(self._job)
            self._job = None

    def run_now(self):
        try:
            return self.stock.expire_overdue()
        except NotImplementedError:
            print("[ExpiryTimer] FID-11 is not built yet, so no stock was expired.")
            return 0
