import re

from bot.type.variable_store import VariableStore


class Url(object):
    youtube_url = 0
    youtube_playlist = 1
    spotify_track = 2
    spotify_playlist = 3
    spotify_artist = 4
    spotify_album = 5
    charts = 6
    term = 7

    youtube = 0
    spotify = 1
    other = 2

    @staticmethod
    def get_all():
        _a = []
        for x in Url().__dir__():
            if isinstance(getattr(Url, x), int):
                _a.append(x)
        return _a

    @staticmethod
    def determine_youtube_type(url):
        if "watch?" in url.lower() or "youtu.be" in url.lower():
            return Url.youtube_url
        elif "playlist" in url.lower():
            return Url.youtube_playlist

    @staticmethod
    def determine_spotify_type(url):
        if "playlist" in url:
            return Url.spotify_playlist
        elif "track" in url:
            return Url.spotify_track
        elif "album" in url:
            return Url.spotify_album
        elif "artist" in url:
            return Url.spotify_artist

    @staticmethod
    def determine_source(url):
        if re.match(VariableStore.youtube_video_pattern, url) is not None:
            return Url.youtube
        elif (
            re.match(VariableStore.spotify_url_pattern, url) is not None
            or re.match(VariableStore.spotify_uri_pattern, url) is not None
        ):
            return Url.spotify
        else:
            return Url.other
