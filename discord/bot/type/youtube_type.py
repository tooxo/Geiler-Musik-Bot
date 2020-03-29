"""
YoutubeType
"""
import re
from typing import Optional

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

    @property
    def id(self) -> Optional[str]:  # pylint: disable=invalid-name
        """
        Extract the id from the url
        @return:
        """
        if not self.valid:
            return None
        return re.search(VariableStore.youtube_video_pattern, self.url).group(
            "id"
        )
