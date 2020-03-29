"""
Queue
"""
import asyncio
from collections import deque
from typing import Any


class Queue(asyncio.Queue):
    """
    Queue
    """

    def __init__(self, *args, **kwargs) -> None:
        self._queue = deque()
        super().__init__(*args, **kwargs)
        self.queue = self._queue
        self._back_queue = deque()
        self._parking_lot = None

    def _get(self) -> Any:
        if self._parking_lot:
            self._back_queue.append(self._parking_lot)
        i = self._queue.popleft()
        self._parking_lot = i
        return i

    def get_last(self) -> Any:
        """
        Get the last entry in the queue
        @return:
        """
        if self._parking_lot:
            self._queue.appendleft(self._parking_lot)
        return self._back_queue.pop()

    def clear(self) -> None:
        """
        Clear the queue
        @return:
        """
        self._queue.clear()

    @property
    def back_queue(self) -> deque:
        """
        Songs, which were already played
        @return:
        """
        return self._back_queue
