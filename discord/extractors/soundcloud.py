import json
import traceback

import aiohttp
import karp.response
import karp.server

import logging_manager
from bot.node_controller.controller import Node
from bot.type.errors import Errors
from bot.type.exceptions import (
    NoResultsFound,
    PlaylistExtractionException,
    SongExtractionException,
)
from bot.type.song import Song


class SoundCloud:
    def __init__(self, node_controller):
        self.log = logging_manager.LoggingManager()
        self.log.debug("[Startup]: Initializing SoundCloud Module . . .")
        self.client = aiohttp.ClientSession()
        self.node_controller = node_controller

    async def soundcloud_search(self, song: Song) -> Song:
        """
        Search SoundCloud
        :param song:
        :return:
        """
        term = getattr(song, "title", getattr(song, "term", None))
        if not term:
            raise NoResultsFound(Errors.no_results_found)
        node: Node = self.node_controller.get_best_node(guild_id=song.guild_id)

        response = await node.client.request(
            "soundcloud_search", term, response=True, timeout=10
        )

        if not response.successful:
            self.log.warning(f"[YT-TERM] {term} {response.text}")
            raise SongExtractionException()

        song_dict: dict = json.loads(response.text)
        song_dict["term"] = term

        song: Song = Song.from_dict(song_dict)
        return song

    async def soundcloud_track(self, url: str):
        try:
            node: Node = self.node_controller.get_best_node()
            response: karp.response.Response = await node.client.request(
                "soundcloud_track", url, response=True, timeout=10
            )
            if not response.successful:
                self.log.warning(f"[SC-TRK] {url} {response.text}")
                raise SongExtractionException()
            response: dict = json.loads(response.text)
            song: Song = Song(
                title=response.get("title", None),
                term=response.get("term", ""),
                link=response.get("link", ""),
                stream=response.get("stream", None),
                duration=response.get("duration", 0),
                loadtime=response.get("loadtime", 0),
                thumbnail=response.get("thumbnail", ""),
                abr=response.get("abr", None),
                codec=response.get("codec", ""),
            )
            if song.duration == 0:
                # try to determine the songs length by content length
                if song.abr:
                    abr = song.abr * 1000 / 8
                    async with aiohttp.request("HEAD", song.stream) as _r:
                        cl = _r.headers.get("Content-Length", "")
                    try:
                        song.duration = int(cl) / abr
                    except ValueError:
                        pass
            return song
        except (TimeoutError, AttributeError) as e:
            self.log.error(traceback.format_exc(e))
            raise SongExtractionException()

    async def soundcloud_playlist(self, url: str):
        try:
            node: Node = self.node_controller.get_best_node()
            response: karp.response.Response = await node.client.request(
                "soundcloud_playlist", url, timeout=10, response=True
            )
            if not response.successful:
                self.log.warning(f"[SC-SET] {url} {response.text}")
                raise PlaylistExtractionException()
            parsed_response = json.loads(response.text)
            songs = []
            for s in parsed_response:
                song: Song = Song()
                song.link = s.get("link", None)
                song.title = s.get("title", "")
                if song.link:
                    songs.append(song)
            return songs
        except (TimeoutError, AttributeError) as e:
            self.log.error(traceback.format_exc())
            raise PlaylistExtractionException(Errors.default)
