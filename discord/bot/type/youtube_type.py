from bot.type.variable_store import VariableStore
import re


class YouTubeType:
    def __init__(self, url):
        self.url = url
        self.VIDEO = "YOUTUBE_VIDEO"
        self.PLAYLIST = "YOUTUBE_PLAYLIST"

    @property
    def valid(self):
        if re.match(VariableStore.youtube_video_pattern, self.url) is not None:
            return True
        return False

    @property
    def id(self):
        if not self.valid:
            return None
        return re.search(VariableStore.youtube_video_pattern, self.url).group("id")
