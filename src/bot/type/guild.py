"""
Guild
"""
import time
from typing import TYPE_CHECKING, Optional

from bot.type.queue import Queue

if TYPE_CHECKING:  # pragma: no cover
    from bot.node_controller.node_voice_client import NodeVoiceClient
    from bot.now_playing_message import NowPlayingMessage
    from bot.type.song import Song
    from discord.channel import VoiceChannel


class Guild:
    """
    Guild
    """

    def __init__(self) -> None:
        self.voice_client: Optional["NodeVoiceClient"] = None
        self.voice_channel: Optional["VoiceChannel"] = None
        self.song_queue: Optional[Queue] = Queue()
        self.now_playing_message: Optional["NowPlayingMessage"] = None
        self.now_playing: Optional["Song"] = None
        self.volume: float = 0.5
        self.full: str = "█"
        self.empty: str = "░"

        self.search_service: str = "basic"
        self.announce: bool = True

        self._queue_lock: bool = False
        self._queue_active_time: int = 0

    def lock_queue(self) -> None:
        """
        Lock the queue
        @return:
        """
        self._queue_lock = True
        self._queue_active_time = time.time()

    def unlock_queue(self) -> None:
        """
        Unlock the queue
        @return:
        """
        self._queue_lock = False
        self._queue_active_time = 0

    @property
    def queue_locked(self) -> bool:
        """
        Check if the queue is locked.
        @return:
        """
        return self._queue_lock and (time.time() - self._queue_active_time) < 10

    async def inflate_from_mongo(self, mongo, guild_id) -> None:
        """
        Inflate from mongo
        :param mongo:
        :param guild_id:
        :return:
        """
        self.volume = await mongo.get_volume(guild_id)
        self.full, self.empty = await mongo.get_chars(guild_id)
        self.search_service = await mongo.get_service(guild_id)
        self.announce = await mongo.get_announce(guild_id)

    @property
    def service(self) -> str:
        """
        Returns the used search service
        :return:
        """
        return self.search_service

    def toggle_announce(self) -> bool:
        """
        Toggles the announcements of songs
        :return Returns the new state
        :rtype bool
        """
        self.announce = not self.announce
        return self.announce

    def __str__(self) -> str:
        return str(self.__dict__)
