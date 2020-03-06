import asyncio
import json
import logging
import random
import socket
import string
import threading
import time
from os import environ

from bot.type.errors import Errors


class Controller:
    def __init__(self, parent):
        self.host = "0.0.0.0"  # nosec
        self.port = 9988
        self.key = environ.get("API_KEY", "API_KEY")

        self.parent = parent

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.socket.bind((self.host, self.port))

        self.server = None

        self.nodes = {}
        self.node_cache = {}

        self.stopped = False

        self.login_logger = logging.Logger("LOGIN", logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        self.login_logger.addHandler(ch)

    @staticmethod
    def random_string(length: int = 16):
        s = ""
        for x in range(length):
            s += random.choice(string.ascii_lowercase)
        return s

    async def connection_handler(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        # start authentication
        _ip = writer.transport.get_extra_info("peername")
        _id = self.random_string(16)
        self.login_logger.info(f"New connection from {_ip}")

        try:
            # receive the api key saved in the node and compares it to the local one
            proposed_api_key = (await reader.read(1024)).decode()[2:]
        except UnicodeDecodeError:
            self.login_logger.info(
                f"Connection declined for {_ip}. Reason: InvalidEncoding"
            )
            writer.close()
            return

        if proposed_api_key != self.key:
            writer.close()
            self.login_logger.info(
                f"Connection declined for {_ip}. Reason: InvalidApiKey"
            )
            return

        writer.write(
            b"A_ACCEPT"
        )  # this notifies the client, that it can transfer the config
        await writer.drain()

        proposed_configuration = await reader.read(
            4096
        )  # this equals 4096 bytes of configuration, which should be enough
        try:
            proposed_configuration = proposed_configuration.decode("UTF-8")
        except UnicodeDecodeError:
            self.login_logger.info(
                f"Connection declined for {_ip}. Reason: InvalidConfEncoding"
            )
            writer.close()
            return

        try:
            configuration = json.loads(proposed_configuration)
            new_node = Node()
            valid_config = new_node.from_dict(configuration)
            if valid_config:
                self.nodes[_id] = new_node
            else:
                self.login_logger.info(
                    f"Connection declined for {_ip}. Reason: InvalidConf"
                )
                return
        except json.JSONDecodeError:
            self.login_logger.info(
                f"Connection declined for {_ip}. Reason: InvalidConf"
            )
            return

        accepted = False
        while not accepted:
            writer.write(f"BT_{environ.get('BOT_TOKEN', '')}".encode())
            await writer.drain()
            if (await reader.read(1024)).decode() == "BT_ACCEPT":
                accepted = True

        is_ready = False
        while not is_ready and not self.stopped:
            await asyncio.sleep(0.1)
            try:
                response = await reader.read(1024)
            except BrokenPipeError:
                self.login_logger.info(f"Connection lost to {_ip}. Reason: BPE")
                break
            if response.decode() == "D_READY":
                self.nodes[_id].writer = writer
                self.nodes[_id].reader = reader
                is_ready = True

        self.login_logger.info(f"Connection established to {_ip}")

        while not self.stopped and is_ready:
            try:
                response = await reader.read(1024)
            except BrokenPipeError:
                del self.nodes[_id]
                self.login_logger.info(f"Connection lost to {_ip}. Reason: BPE")
                break
            if not response:
                break
            self._handle_response(response=response.decode())
            await asyncio.sleep(0.1)
        self.login_logger.info(f"Connection lost to {_ip}. Reason: Basic")
        writer.close()

    async def start_server(self):
        self.server = await asyncio.start_server(
            self.connection_handler, self.host, self.port
        )
        asyncio.ensure_future(self.server.serve_forever())

    def _handle_response(self, response: str):
        if response.count("#S_") > 1:
            response = response.split("#S_")[1:]
        else:
            response = [response]
        for response in response:
            if response.startswith("#S_AFT_"):
                data: dict = json.loads(response[7:])
                guild_id = data.get("guild_id", None)
                if guild_id:
                    if self.parent.guilds[guild_id].voice_client:
                        self.parent.guilds[guild_id].voice_client.after()
            elif response.startswith("#S_BR_"):
                response = json.loads(response[6:])
                if self.parent.guilds[response["guild_id"]].now_playing_message:
                    self.parent.guilds[
                        response["guild_id"]
                    ].now_playing_message.bytes_read = response["bytes_read"]

    def get_best_node(self, guild_id: int = None, black_list=None):
        if black_list is None:
            black_list = list()
        if guild_id is not None:
            if guild_id in self.node_cache.keys():
                node = self.nodes.get(self.node_cache[guild_id], None)
                if node:
                    if node.is_ready():
                        return node
        if len(black_list) < len(self.nodes):
            node: Node = self.nodes[random.choice(list(self.nodes.keys()))]
            while node in black_list:
                node: Node = self.nodes[random.choice(list(self.nodes.keys()))]
            if not node.is_ready():
                black_list.append(node)
                return self.get_best_node(black_list=black_list)
            self.node_cache[guild_id] = node
            return node
        raise NoNodeReadyException(Errors.backend_down)


class NoNodeReadyException(Exception):
    pass


class Node:
    def __init__(self):
        self.ip = ""
        self.port = 0
        self.name = ""
        self.reader: asyncio.StreamReader
        self.writer: asyncio.StreamWriter

    def is_ready(self):
        if hasattr(self, "reader") and hasattr(self, "writer"):
            return True
        return False

    def from_dict(self, d: dict):
        self.ip = d.get("ip", None)
        self.port = d.get("port", None)
        self.name = d.get("name", None)
        return (
            self.ip is not None
            and self.port is not None
            and self.name is not None
        )
