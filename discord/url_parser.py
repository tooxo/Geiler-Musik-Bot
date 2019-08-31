# -*- coding: utf-8 -*-

import re
from variable_store import VariableStore


class SpotifyType:
    def __init__(self, url):
        self.url = url
        self.URI = "SPOTIFY_URI"
        self.URL = "SPOTIFY_URL"

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
                return self.URL
            if re.match(VariableStore.spotify_uri_pattern, self.url) is not None:
                return self.URI
        return None

    @property
    def id(self):
        if self.type is self.URL:
            return re.search(VariableStore.spotify_url_pattern, self.url).group("id")
        if self.type is self.URI:
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
