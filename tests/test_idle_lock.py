"""SEC-3: 15-minute idle lock (Janae)."""
import unittest

from app.logic.idle_lock import IDLE_MS, IdleLock


class FakeRoot:
    def __init__(self):
        self.jobs = {}
        self.next_id = 1

    def after(self, ms, func):
        job = self.next_id
        self.next_id += 1
        self.jobs[job] = (ms, func)
        return job

    def after_cancel(self, job):
        self.jobs.pop(job, None)


class IdleLockTests(unittest.TestCase):
    def setUp(self):
        self.root, self.locked = FakeRoot(), []
        self.lock = IdleLock(self.root, lambda: self.locked.append(True))

    def test_timeout_is_15_minutes(self):
        self.assertEqual(IDLE_MS, 15 * 60 * 1000)
        self.lock.start()
        self.assertEqual(list(self.root.jobs.values())[0][0], 900_000)

    def test_locks_when_idle(self):
        self.lock.start()
        list(self.root.jobs.values())[0][1]()                                # the 15 minutes pass
        self.assertEqual(self.locked, [True])

    def test_activity_restarts_the_countdown(self):
        self.lock.start()
        self.lock.reset()
        self.assertEqual(len(self.root.jobs), 1)                             # old countdown cancelled
        self.assertEqual(self.locked, [])

    def test_activity_after_stop_does_not_restart(self):
        self.lock.start()
        self.lock.stop()
        self.lock.reset()                                                    # e.g. mouse moved on the login screen
        self.assertEqual(self.root.jobs, {})

    def test_stop_cancels(self):
        self.lock.start()
        self.lock.stop()
        self.assertEqual(self.root.jobs, {})


if __name__ == "__main__":
    unittest.main()
