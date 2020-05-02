"""
YoutubeType
"""
import re

from bot.type.variable_store import VariableStore


class YouTubeType:
    """
    YouTubeType
    """

    VIDEO = "YOUTUBE_VIDEO"
    PLAYLIST = "YOUTUBE_PLAYLIST"

    def __init__(self, url: str) -> None:
        self.url = url

    @property
    def valid(self) -> bool:
        """
        Check if a YouTube url is valid
        @return:
        """
        if re.match(VariableStore.youtube_video_pattern, self.url):
            return True
        return False
