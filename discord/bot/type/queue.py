import asyncio
from collections import deque


class Queue(asyncio.Queue):
    def __init__(self, *args, **kwargs):
        self._queue = deque()
        super().__init__(*args, **kwargs)
        self.queue = self._queue
        self._back_queue = deque()
        self._parking_lot = None

    def _get(self):
        if self._parking_lot:
            self._back_queue.append(self._parking_lot)
        i = self._queue.popleft()
        self._parking_lot = i
        return i

    def get_last(self):
        if self._parking_lot:
            self._queue.appendleft(self._parking_lot)
        return self._back_queue.pop()

    def clear(self):
        self._queue.clear()

    @property
    def back_queue(self):
        return self._back_queue
