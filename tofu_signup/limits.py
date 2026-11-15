"""In-memory counters shared by all sessions. They reset when the app restarts."""

import threading
import time
from collections import deque


class Limits:
    def __init__(self, invite_max_fails: int, creates_per_hour: int):
        self._lock = threading.Lock()
        self._invite_max_fails = invite_max_fails
        self._invite_fails = 0
        self._creates_per_hour = creates_per_hour
        self._creates: deque[float] = deque()

    def invite_locked(self) -> bool:
        with self._lock:
            return self._invite_fails >= self._invite_max_fails

    def record_invite_fail(self) -> None:
        with self._lock:
            self._invite_fails += 1

    def try_reserve_create(self) -> bool:
        """Count one creation attempt against the hourly cap. Returns False if the cap is reached."""
        now = time.monotonic()
        with self._lock:
            while self._creates and now - self._creates[0] > 3600:
                self._creates.popleft()
            if len(self._creates) >= self._creates_per_hour:
                return False
            self._creates.append(now)
            return True
