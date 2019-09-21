# -*- coding: utf-8 -*-

import re
from variable_store import VariableStore

URI = "SPOTIFY_URI"
URL = "SPOTIFY_URL"


class SpotifyType:
    def __init__(self, url):
        self.url = url
        self.spotify_uri = "SPOTIFY_URI"
        self.spotify_url = "SPOTIFY_URL"

    @property
    def valid(self):
        if re.match(VariableStore.spotify_url_pattern, self.url) is not None:
            return True
        if re.match(VariableStore.spotify_uri_pattern, self.url) is not None:
            return True
        return False

    @property
    def type(self):
        if self.valid:
            if re.match(VariableStore.spotify_url_pattern, self.url) is not None:
                return self.spotify_url
            if re.match(VariableStore.spotify_uri_pattern, self.url) is not None:
                return self.spotify_uri
        return None

    @property
    def id(self):
        if self.type is self.spotify_url:
            return re.search(VariableStore.spotify_url_pattern, self.url).group("id")
        if self.type is self.spotify_uri:
            return re.search(VariableStore.spotify_uri_pattern, self.url).group("id")
        if self.type is None:
            return None


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
