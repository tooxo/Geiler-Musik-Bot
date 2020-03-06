import asyncio
import json

import aiohttp
import async_timeout

import logging_manager
from bot.node_controller.controller import Controller
from bot.type.errors import Errors
from bot.type.exceptions import BackendDownException, BasicError, NoResultsFound
from bot.type.song import Song
from bot.type.variable_store import VariableStore

log = logging_manager.LoggingManager()


class YoutubeDLLogger(object):
    @staticmethod
    def debug(msg):
        if "youtube:search" in msg and "query" in msg:
            log.debug(
                logging_manager.debug_info(
                    "[YouTube Search] Searched Term: '"
                    + msg.split('"')[1].split('"')[-1]
                    + "'"
                )
            )

    @staticmethod
    def warning(msg):
        log.warning(logging_manager.debug_info(msg))

    @staticmethod
    def error(msg):
        log.error(logging_manager.debug_info(msg))


class Youtube:
    def __init__(self, node_controller: Controller):
        log.debug("[Startup]: Initializing YouTube Module . . .")
        self.session = aiohttp.ClientSession()
        self.node_controller = node_controller

        self.term_url = "http://{}:{}/research/youtube_search"
        self.url_url = "http://{}:{}/research/youtube_video"
        self.playlist_url = "http://{}:{}/research/youtube_playlist"

    async def http_get(self, url) -> str:
        try:
            with async_timeout.timeout(5):
                async with self.session.get(url=url) as re:
                    return await re.text()
        except asyncio.TimeoutError:
            raise BasicError(Errors.default)

    async def http_post(self, url, data) -> str:
        try:
            with async_timeout.timeout(10):
                async with self.session.post(url=url, data=data) as re:
                    if re.status != 200:
                        if re.status == 500:
                            raise BackendDownException(Errors.backend_down)
                        raise BasicError(await re.text())
                    return await re.text()
        except asyncio.TimeoutError:
            raise BasicError(Errors.default)

    async def youtube_term(self, song: (Song, str), service: str):
        log.info(f'Using Search Service "{service}"')
        if isinstance(song, Song):
            if song.term:
                term = song.term
            elif song.title:
                term = song.title
            else:
                raise NoResultsFound(Errors.no_results_found)
        else:
            term = song

        node = self.node_controller.get_best_node(guild_id=song.guild_id)

        url = await self.http_post(
            self.term_url.format(node.ip, node.port),
            json.dumps({"service": service, "term": term}),
        )

        url = VariableStore.youtube_url_to_id(url)
        sd = await self.http_post(
            url=self.url_url.format(node.ip, node.port), data=url
        )
        song_dict: dict = json.loads(sd)
        song_dict["term"] = term

        song: Song = Song.from_dict(song_dict)
        return song

    async def youtube_url(self, url, guild_id: int):
        url = VariableStore.youtube_url_to_id(url)
        node = self.node_controller.get_best_node(guild_id)
        sd = await self.http_post(
            url=self.url_url.format(node.ip, node.port), data=url
        )

        song_dict: dict = json.loads(sd)

        if song_dict == {}:
            raise NoResultsFound(Errors.no_results_found)
        song: Song = Song.from_dict(song_dict)
        return song

    async def youtube_playlist(self, url):
        url = VariableStore.youtube_url_to_id(url)
        node = self.node_controller.get_best_node()
        try:
            sd = await self.http_post(
                url=self.playlist_url.format(node.ip, node.port), data=url
            )
        except BasicError:
            return []

        songs = []
        for t in json.loads(sd):
            s = Song()
            s.title = t["title"]
            s.link = t["link"]
            songs.append(s)

        return songs
