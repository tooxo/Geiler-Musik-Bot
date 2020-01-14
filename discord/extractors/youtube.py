from asyncio import TimeoutError
import aiohttp
import async_timeout
import logging_manager
from extractors import mongo
from bot.type.errors import Errors
from bot.type.variable_store import VariableStore
from bot.type.song import Song
from bot.type.error import Error
import json

log = logging_manager.LoggingManager()


class YoutubeDLLogger(object):
    def debug(self, msg):
        if "youtube:search" in msg and "query" in msg:
            log.debug(
                logging_manager.debug_info(
                    "[YouTube Search] Searched Term: '"
                    + msg.split('"')[1].split('"')[-1]
                    + "'"
                )
            )

    def warning(self, msg):
        log.warning(logging_manager.debug_info(msg))

    def error(self, msg):
        log.error(logging_manager.debug_info(msg))


class Youtube:
    def __init__(self, mongo_client: mongo):
        log.debug("[Startup]: Initializing YouTube Module . . .")
        self.session = aiohttp.ClientSession()
        self.mongo = mongo_client

        self.term_url = "http://parent:8008/research/youtube_search"
        self.url_url = "http://parent:8008/research/youtube_video"
        self.playlist_url = "http://parent:8008/research/youtube_playlist"

    async def http_get(self, url):
        try:
            with async_timeout.timeout(5):
                async with self.session.get(url=url) as re:
                    return re.text()
        except TimeoutError:
            return Error(True, Errors.default)

    async def http_post(self, url, data):
        try:
            with async_timeout.timeout(10):
                async with self.session.post(url=url, data=data) as re:
                    if re.status != 200:
                        if re.status == 500:
                            return Error(True, Errors.backend_down)
                        return Error(True, await re.text())
                    return await re.text()
        except TimeoutError:
            return Error(True, Errors.default)

    async def youtube_term(self, term):
        url = await self.http_post(self.term_url, term)

        if isinstance(url, Error):
            return url

        url = VariableStore.youtube_url_to_id(url)

        sd = await self.http_post(url=self.url_url, data=url)
        if isinstance(sd, Error):
            return sd
        song_dict: dict = json.loads(sd)
        song_dict["term"] = term

        song: Song = Song.from_dict(song_dict)
        return song

    async def youtube_url(self, url):
        url = VariableStore.youtube_url_to_id(url)
        sd = await self.http_post(url=self.url_url, data=url)

        if isinstance(sd, Error):
            return sd

        song_dict: dict = json.loads(sd)

        if song_dict == {}:
            return Error(Errors.default)
        song: Song = Song.from_dict(song_dict)
        return song

    async def youtube_playlist(self, url):
        url = VariableStore.youtube_url_to_id(url)
        sd = await self.http_post(url=self.playlist_url, data=url)

        if isinstance(sd, Error):
            return []

        songs = []
        for t in json.loads(sd):
            s = Song()
            s.title = t["title"]
            s.link = t["link"]
            songs.append(s)

        return songs
