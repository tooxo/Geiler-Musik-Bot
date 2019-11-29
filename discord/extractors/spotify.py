import json
import asyncio
import async_timeout
import aiohttp
import base64
import os
import logging_manager
from url_parser import SpotifyType
from song_store import SpotifyObj


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
            async with self.session.post(url, headers=header, data=body) as response:
                return await response.text()

    async def request_get(self, url, header):
        with async_timeout.timeout(3):
            async with self.session.get(url, headers=header) as response:
                return await response.text()

    async def invalidate_token(self):
        if self.token is not "":
            for x in range(1, 3000):
                try:
                    await asyncio.sleep(x)
                except InterruptedError:
                    self.token = ""
                    break
            self.token = ""

    async def request_token(self):
        if self.token is "":
            string = self.client_id + ":" + self.client_secret
            enc = base64.b64encode(string.encode())
            url = "https://accounts.spotify.com/api/token"
            header = {
                "Authorization": "Basic " + enc.decode(),
                "Content-Type": "application/x-www-form-urlencoded",
            }
            payload = "grant_type=client_credentials&undefined="
            test = await self.request_post(url, header, payload)
            asyncio.ensure_future(self.invalidate_token())
            self.token = json.loads(test)["access_token"]
            return self.token
        else:
            return self.token

    async def spotify_track(self, track_url):
        token = await self.request_token()
        track = SpotifyType(track_url)
        if not track.valid:
            return None
        url = "https://api.spotify.com/v1/tracks/" + track.id
        header = {"Authorization": "Bearer " + token}
        result = await self.request_get(url, header)
        result = json.loads(result)
        return SpotifyObj(
            title=result["artists"][0]["name"] + " - " + result["name"],
            image_url=result["album"]["images"][0]["url"],
        )
        # return result["artists"][0]["name"] + " - " + result["name"]

    async def spotify_playlist(self, playlist_url):
        token = await self.request_token()
        playlist = SpotifyType(playlist_url)
        if not playlist.valid:
            return []
        url = (
            "https://api.spotify.com/v1/playlists/"
            + playlist.id
            + "/tracks?limit=100&offset=0"
        )
        header = {"Authorization": "Bearer " + token}
        result = await self.request_get(url, header)
        js = json.loads(result)
        t_list = []
        more = True
        while more is True:
            try:
                for track in js["items"]:
                    if track["is_local"]:
                        try:
                            t_list.append(
                                track["track"]["artists"][0]["name"]
                                + " - "
                                + track["track"]["name"]
                            )
                        except (IndexError, KeyError):
                            # Probably invalid local file
                            continue
                    else:
                        t_list.append(
                            track["track"]["album"]["artists"][0]["name"]
                            + " - "
                            + track["track"]["name"]
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
        return t_list

    async def spotify_album(self, album_url):
        token = await self.request_token()
        album = SpotifyType(album_url)
        if not album.valid:
            return []
        url = "https://api.spotify.com/v1/albums/" + album.id + "/tracks?limit=50"
        header = {"Authorization": "Bearer " + token}
        result = await self.request_get(url, header)
        js = json.loads(result)
        track_list = []
        for item in js["items"]:
            artist = item["artists"][0]["name"]
            song = item["name"]
            track_list.append(artist + " - " + song)
        return track_list

    async def spotify_artist(self, artist_url):
        token = await self.request_token()
        artist = SpotifyType(artist_url)
        if not artist.valid:
            return []
        url = (
            "https://api.spotify.com/v1/artists/" + artist.id + "/top-tracks?country=DE"
        )
        header = {"Authorization": "Bearer " + token}
        result = await self.request_get(url, header)
        js = json.loads(result)
        track_list = []
        for item in js["tracks"]:
            artist = item["artists"][0]["name"]
            song = item["name"]
            track_list.append(artist + " - " + song)
        return track_list
