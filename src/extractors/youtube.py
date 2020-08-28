"""
YouTube
"""
import json
from typing import List

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

LOG = logging_manager.LoggingManager()


class Youtube:
    """
    YouTube
    """

    def __init__(self, node_controller: Controller):
        LOG.debug("[Startup]: Initializing YouTube Module . . .")
        self.session = aiohttp.ClientSession()
        self.node_controller = node_controller

    async def youtube_term(self, song: Song, service: str) -> Song:
        """
        Extract information from YouTube by Term
        @param song:
        @param service: 
        @return:
        """
        term: str = song.title or song.term
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
            raise NoResultsFound(
                f"Term: {term} | Server Response :{response.text}", )
        url = response.text

        url = VariableStore.youtube_url_to_id(url)

        response = await node.client.request(
            "youtube_video", url, response=True, timeout=10
        )

        if not response.successful:
            LOG.warning(f"[YT-TERM] {url} {response.text}")
            raise SongExtractionException()

        song_dict: dict = json.loads(response.text)
        song_dict["term"] = term

        song: Song = Song.from_dict(song_dict)
        return song

    async def youtube_url(self, url, guild_id: int) -> Song:
        """
        Extract information from YouTube by url
        @param url:
        @param guild_id:
        @return:
        """
        url = VariableStore.youtube_url_to_id(url)
        node: Node = self.node_controller.get_best_node(guild_id)

        response = await node.client.request(
            "youtube_video", url, response=True, timeout=10
        )

        if not response.successful:
            LOG.warning(f"[YT-URL] {url} {response.text}")
            raise SongExtractionException()

        song_dict: dict = json.loads(response.text)

        if song_dict == {}:
            raise NoResultsFound(Errors.no_results_found)
        song: Song = Song.from_dict(song_dict)
        return song

    async def youtube_playlist(self, url: str) -> List[Song]:
        """
        Extract information from YouTube by Playlist url
        @param url:
        @return:
        """
        url = VariableStore.youtube_url_to_id(url)
        node: Node = self.node_controller.get_best_node()

        response = await node.client.request(
            "youtube_playlist", url, response=True, timeout=10
        )

        if not response.successful:
            raise PlaylistExtractionException(response.text)

        songs = []
        for track in json.loads(response.text):
            song = Song()
            song.title = track["title"]
            song.link = track["link"]
            songs.append(song)

        return songs
