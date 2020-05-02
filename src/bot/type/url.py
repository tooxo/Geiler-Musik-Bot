"""
Url
"""
import re
from typing import Optional

from bot.type.variable_store import VariableStore


class Url:
    """
    Url
    """

    youtube_url = 0
    youtube_playlist = 1
    spotify_track = 2
    spotify_playlist = 3
    spotify_artist = 4
    spotify_album = 5
    charts = 6
    term = 7

    soundcloud_track = 12
    soundcloud_set = 32

    youtube = 0
    spotify = 1
    soundcloud = 3
    other = 2

    @staticmethod
    def determine_youtube_type(url: str) -> Optional[int]:
        """
        Determine type of YouTube url
        @param url:
        @return:
        """
        if "watch?" in url.lower() or "youtu.be" in url.lower():
            return Url.youtube_url
        if "playlist" in url.lower():
            return Url.youtube_playlist
        return None

    @staticmethod
    def determine_spotify_type(url: str) -> Optional[int]:
        """
        Determine type of Spotify url
        @param url:
        @return:
        """
        if "playlist" in url:
            return Url.spotify_playlist
        if "track" in url:
            return Url.spotify_track
        if "album" in url:
            return Url.spotify_album
        if "artist" in url:
            return Url.spotify_artist
        return None

    @staticmethod
    def determine_soundcloud_type(url: str) -> Optional[int]:
        """
        Determine type of SoundCloud url
        @param url:
        @return:
        """
        if re.match(VariableStore.soundcloud_url_pattern, url):
            return Url.soundcloud_track
        if re.match(VariableStore.soundcloud_sets_pattern, url):
            return Url.soundcloud_set
        return None

    @staticmethod
    def determine_source(url: str) -> int:
        """
        Determine general type of url
        @param url:
        @return:
        """
        if re.match(VariableStore.youtube_video_pattern, url):
            return Url.youtube
        if re.match(VariableStore.spotify_url_pattern, url) or re.match(
            VariableStore.spotify_uri_pattern, url
        ):
            return Url.spotify
        if re.match(VariableStore.soundcloud_url_pattern, url) or re.match(
            VariableStore.soundcloud_sets_pattern, url
        ):
            return Url.soundcloud
        return Url.other
