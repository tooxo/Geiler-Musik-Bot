import asyncio
from collections import deque


class Queue(asyncio.Queue):
    def __init__(self, *args, **kwargs):
        self._queue = deque()
        super().__init__(*args, **kwargs)
        self.queue = self._queue
