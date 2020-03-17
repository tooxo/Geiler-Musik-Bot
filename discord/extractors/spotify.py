import asyncio
import base64
import json
import os

import aiohttp
import async_timeout

import logging_manager
from bot.type.exceptions import (
    PlaylistExtractionException,
    SongExtractionException,
)
from bot.type.spotify_song import SpotifySong
from bot.type.spotify_type import SpotifyType


class Spotify:
    def __init__(self):
        self.log = logging_manager.LoggingManager()
        self.log.debug("[Startup]: Initializing Spotify Module . . .")
        self.session = aiohttp.ClientSession()
        self.token = ""
        self.client_id = os.environ["SPOTIFY_ID"]
        self.client_secret = os.environ["SPOTIFY_SECRET"]

    async def request_post(self, url, header=None, body=None):
        with async_timeout.timeout(3):
            async with self.session.post(
                url, headers=header, data=body
            ) as response:
                return await response.text()

    async def request_get(self, url, header):
        with async_timeout.timeout(3):
            async with self.session.get(url, headers=header) as response:
                return await response.text()

    def _invalidate_token(self) -> None:
        self.log.info("Spotify Token Invalidated.")
        self.token = ""

    async def _request_token(self) -> str:
        if self.token == "":
            try:
                string = self.client_id + ":" + self.client_secret
                enc = base64.b64encode(string.encode())
                url = "https://accounts.spotify.com/api/token"
                header = {
                    "Authorization": f"Basic {enc.decode()}",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
                payload = "grant_type=client_credentials"
                token_data = await self.request_post(url, header, payload)
                asyncio.get_event_loop().call_later(
                    3000, self._invalidate_token
                )
                self.token = json.loads(token_data)["access_token"]
                self.log.logger.info(f"Got new Spotify Token: {self.token}")
            except asyncio.TimeoutError:
                return await self._request_token()
        return self.token

    async def spotify_track(self, track_url):
        token = await self._request_token()
        track = SpotifyType(track_url)
        if not track.valid:
            raise SongExtractionException()
        url = "https://api.spotify.com/v1/tracks/" + track.id
        header = {"Authorization": "Bearer " + token}
        result = await self.request_get(url, header)
        result = json.loads(result)
        if "error" in result:
            raise SongExtractionException()
        return SpotifySong(
            title=result["artists"][0]["name"] + " - " + result["name"],
            image_url=result["album"]["images"][0]["url"],
            song_name=result["name"],
            artist=result["artists"][0]["name"],
        )

    async def spotify_playlist(self, playlist_url):
        token = await self._request_token()
        playlist = SpotifyType(playlist_url)
        if not playlist.valid:
            raise PlaylistExtractionException()
        url = (
            "https://api.spotify.com/v1/playlists/"
            + playlist.id
            + "/tracks?limit=100&offset=0"
        )
        header = {"Authorization": "Bearer " + token}
        result = await self.request_get(url, header)
        js = json.loads(result)
        if "error" in js:
            raise PlaylistExtractionException()
        t_list = []
        more = True
        while more is True:
            try:
                for track in js["items"]:
                    if track["is_local"]:
                        try:
                            t_list.append(
                                SpotifySong(
                                    title=track["track"]["artists"][0]["name"]
                                    + " - "
                                    + track["track"]["name"],
                                    image_url=None,
                                    song_name=track["track"]["name"],
                                    artist=track["track"]["artists"][0]["name"],
                                )
                            )
                        except (IndexError, KeyError):
                            # Probably invalid local file
                            continue
                    else:
                        t_list.append(
                            SpotifySong(
                                title=track["track"]["album"]["artists"][0][
                                    "name"
                                ]
                                + " - "
                                + track["track"]["name"],
                                image_url=track["track"]["album"]["images"][0][
                                    "url"
                                ],
                                song_name=track["track"]["name"],
                                artist=track["track"]["artists"][0]["name"],
                            )
                        )

                if js["next"] is None:
                    more = False
                else:
                    url = js["next"]
                    result = await self.request_get(url, header)
                    js = json.loads(result)
            except KeyError as key_error:
                self.log.warning(
                    logging_manager.debug_info(str(key_error) + " " + str(js))
                )
                if "error" in js:
                    self.token = ""
                more = False

            if not t_list:
                raise PlaylistExtractionException()
        return t_list

    async def spotify_album(self, album_url):
        token = await self._request_token()
        album = SpotifyType(album_url)
        if not album.valid:
            raise PlaylistExtractionException()
        url = (
            "https://api.spotify.com/v1/albums/" + album.id + "/tracks?limit=50"
        )
        header = {"Authorization": "Bearer " + token}
        result = await self.request_get(url, header)
        js = json.loads(result)
        if "error" in js:
            raise PlaylistExtractionException()
        track_list = []
        for item in js["items"]:
            artist = item["artists"][0]["name"]
            song = item["name"]
            track_list.append(artist + " - " + song)
        if not track_list:
            raise PlaylistExtractionException()
        return track_list

    async def spotify_artist(self, artist_url):
        token = await self._request_token()
        artist = SpotifyType(artist_url)
        if not artist.valid:
            raise PlaylistExtractionException()
        url = (
            "https://api.spotify.com/v1/artists/"
            + artist.id
            + "/top-tracks?country=DE"
        )
        header = {"Authorization": "Bearer " + token}
        result = await self.request_get(url, header)
        js = json.loads(result)
        if "error" in js:
            raise PlaylistExtractionException()
        track_list = []
        for item in js["tracks"]:
            artist = item["artists"][0]["name"]
            song = item["name"]
            track_list.append(artist + " - " + song)
        if not track_list:
            raise PlaylistExtractionException
        return track_list
