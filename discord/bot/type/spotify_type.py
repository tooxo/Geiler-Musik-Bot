from bot.type.variable_store import VariableStore
import re


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
