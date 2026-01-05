import asyncio
from typing import List, Optional

from core.downloader import Downloader


class QueueItem:
    def __init__(self, downloader: Downloader):
        self.downloader = downloader
        self.task: Optional[asyncio.Task] = None
        self.completed = False
        self.failed = False
        self.error: Optional[Exception] = None


class DownloadQueue:
    """
    IDM-style download queue manager.
    """

    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self.queue: List[QueueItem] = []
        self._running = False
        self._semaphore = asyncio.Semaphore(max_concurrent)

    # -------------------- PUBLIC API --------------------

    def add(self, downloader: Downloader):
        item = QueueItem(downloader)
        self.queue.append(item)
        return item

    async def start(self):
        if self._running:
            return

        self._running = True
        await self._run_queue()

    def stop(self):
        self._running = False
        for item in self.queue:
            if item.task and not item.task.done():
                item.downloader.stop()

    # -------------------- INTERNAL --------------------

    async def _run_queue(self):
        tasks = []

        for item in self.queue:
            if item.completed:
                continue

            task = asyncio.create_task(self._run_item(item))
            item.task = task
            tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)
        self._running = False

    async def _run_item(self, item: QueueItem):
        async with self._semaphore:
            if not self._running:
                return

            try:
                await item.downloader.start()
                item.completed = True
            except Exception as e:
                item.failed = True
                item.error = e
