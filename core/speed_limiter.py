import time
import asyncio


class SpeedLimiter:
    """
    Limits download speed to a maximum bytes/sec.
    Can be shared across multiple download chunks.
    """

    def __init__(self, max_bytes_per_sec: int = 0):
        """
        :param max_bytes_per_sec: 0 = unlimited
        """
        self.max_bps = max_bytes_per_sec
        self._bytes_sent = 0
        self._window_start = time.monotonic()
        self._lock = asyncio.Lock()

    async def throttle(self, bytes_count: int):
        """
        Call this after writing bytes to disk.
        """
        if self.max_bps <= 0:
            return  # unlimited

        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._window_start

            self._bytes_sent += bytes_count

            if elapsed >= 1:
                # Reset window every second
                self._bytes_sent = 0
                self._window_start = now
                return

            if self._bytes_sent > self.max_bps:
                sleep_time = 1 - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                self._bytes_sent = 0
                self._window_start = time.monotonic()
