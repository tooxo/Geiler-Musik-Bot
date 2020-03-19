import json

import aiohttp

import logging_manager
from bot.node_controller.controller import Controller, Node
from bot.type.errors import Errors
from bot.type.exceptions import (
    NoResultsFound,
    PlaylistExtractionException,
    SongExtractionException,
)
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

    async def youtube_term(self, song: (Song, str), service: str):
        log.info(f'Using Search Service "{service}"')

        term = getattr(song, "title", getattr(song, "term", None))
        if not term:
            raise NoResultsFound(Errors.no_results_found)

        node: Node = self.node_controller.get_best_node(guild_id=song.guild_id)

        response = await node.client.request(
            "youtube_search",
            json.dumps({"service": service, "term": term}),
            response=True,
            timeout=10,
        )

        if not response.successful:
            raise NoResultsFound(response.text)
        url = response.text

        url = VariableStore.youtube_url_to_id(url)

        response = await node.client.request(
            "youtube_video", url, response=True, timeout=10
        )

        if not response.successful:
            log.warning(f"[YT-TERM] {url} {response.text}")
            raise SongExtractionException()

        song_dict: dict = json.loads(response.text)
        song_dict["term"] = term

        song: Song = Song.from_dict(song_dict)
        return song

    async def youtube_url(self, url, guild_id: int):
        url = VariableStore.youtube_url_to_id(url)
        node: Node = self.node_controller.get_best_node(guild_id)

        response = await node.client.request(
            "youtube_video", url, response=True, timeout=10
        )

        if not response.successful:
            log.warning(f"[YT-URL] {url} {response.text}")
            raise SongExtractionException()

        song_dict: dict = json.loads(response.text)

        if song_dict == {}:
            raise NoResultsFound(Errors.no_results_found)
        song: Song = Song.from_dict(song_dict)
        return song

    async def youtube_playlist(self, url):
        url = VariableStore.youtube_url_to_id(url)
        node: Node = self.node_controller.get_best_node()

        response = await node.client.request(
            "youtube_playlist", url, response=True, timeout=10
        )

        if not response.successful:
            raise PlaylistExtractionException()

        songs = []
        for t in json.loads(response.text):
            s = Song()
            s.title = t["title"]
            s.link = t["link"]
            songs.append(s)

        return songs
