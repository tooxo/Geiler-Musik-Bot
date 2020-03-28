"""
Controller
"""
import asyncio
import json
import logging
import random
import string
from os import environ
from typing import Dict, Optional

from karp.request import Request
from karp.response import Response
from karp.server import Client, KARPServer

from bot.type.errors import Errors
from bot.type.exceptions import NoNodeReadyException
from bot.type.guild import Guild


class Controller:
    def __init__(self, parent):
        self.host = "0.0.0.0"
        self.port = "9988"
        self.key = environ.get("API_KEY", "API_KEY")

        self.parent = parent
        self.guilds: Dict[int, Guild] = parent.guilds

        self.nodes = {}
        self.node_cache = {}

        self.login_logger = logging.Logger("LOGIN", logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        self.login_logger.addHandler(ch)
        self.server = KARPServer(self.host, self.port)
        self.server.logger.setLevel(logging.INFO)

    @staticmethod
    def random_string(length: int = 16) -> str:
        """
        Generates a random string
        :param length:
        :return:
        """
        s = ""
        for x in range(length):
            s += random.choice(string.ascii_lowercase)
        return s

    async def _on_new_connection(self, client: Client) -> None:
        node: Node = Node(client)
        try:

            response: Response = await node.client.request(
                "identify", "", True, 10
            )
            if not response.successful:
                raise asyncio.TimeoutError()
            try:
                content: dict = json.loads(response.text)
            except json.JSONDecodeError:
                raise asyncio.TimeoutError()

            try:
                api_key = content["API_KEY"]
            except (TypeError, KeyError):
                raise asyncio.TimeoutError()

            if api_key != self.key:
                raise asyncio.TimeoutError()

            response: Response = await node.client.request(
                "accepted",
                json.dumps({"DISCORD_API_KEY": environ.get("BOT_TOKEN", "")}),
                True,
                60,
            )
        except asyncio.TimeoutError:
            node.client.writer.close()
            return
        if response.text == "1":
            self.login_logger.info("Connection Established.")
            self.nodes[node.id] = node

    def _on_connection_lost(self, client: Client):
        if client.id in self.nodes:
            del self.nodes[client.id]

    async def start_server(self):
        self.server.on_new_connection = self._on_new_connection
        self.server.on_connection_lost = self._on_connection_lost
        self._add_routes()
        asyncio.ensure_future(self.server.start())

    def _add_routes(self) -> None:
        @self.server.add_route(route="discord_after")
        async def _discord_after(request: Request) -> None:
            data: dict = json.loads(request.text)
            guild_id = data.get("guild_id", None)
            if guild_id:
                if self.guilds[guild_id].voice_client:
                    # noinspection PyProtectedMember
                    self.guilds[guild_id].voice_client._is_connected = data.get(
                        "connected", True
                    )

                    await self.guilds[guild_id].voice_client.after()

        @self.server.add_route(route="discord_bytes")
        def _discord_bytes(request: Request) -> None:
            response = json.loads(request.text)
            if self.guilds[response["guild_id"]].now_playing_message:
                self.guilds[
                    response["guild_id"]
                ].now_playing_message.bytes_read = response["bytes_read"]

    def get_best_node(self, guild_id: Optional[int] = None):
        """
        Gets the best node
        :param guild_id: get node designated to guild
        :return:
        """
        if guild_id is not None:
            if guild_id in self.node_cache.keys():
                node = self.nodes.get(self.node_cache[guild_id], None)
                if node:
                    return node
        if len(self.nodes) > 0:
            node = self.nodes[random.choice(list(self.nodes.keys()))]
            if guild_id:
                self.node_cache[guild_id] = node
            return node
        raise NoNodeReadyException(Errors.backend_down)


class Node:
    def __init__(self, client: Client):
        self.name = ""
        self.id = client.id

        self.client: Client = client

        self.reader: asyncio.StreamReader = client.reader
        self.writer: asyncio.StreamWriter = client.writer
