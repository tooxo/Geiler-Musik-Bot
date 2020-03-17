"""
NodeVoiceClient
"""
import asyncio
import inspect
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import discord
from bot.node_controller.controller import Controller, Node
from bot.type.song import Song
from discord.ext import commands


class NodeVoiceChannel(discord.VoiceChannel):
    def __init__(
        self, *, state, guild, data, node: Node, node_controller: Controller
    ):
        super().__init__(state=state, guild=guild, data=data)
        self.node: Node = node
        self.node_controller = node_controller

    async def connect(self, *, timeout=60.0, reconnect=True):
        document = {
            "guild_id": self.guild.id,
            "voice_channel_id": self.id,
            "reconnect": True,
        }
        await self.node.client.request(
            "discord_connect", json.dumps(document), response=False
        )
        return NodeVoiceClient(
            self.id, self.guild.id, self.node, self.node_controller
        )

    @staticmethod
    def from_channel(
        voice_channel: discord.VoiceChannel, node_controller: Controller
    ):
        return NodeVoiceChannel(
            state=voice_channel._state,
            guild=voice_channel.guild,
            data={
                "name": voice_channel.name,
                "id": voice_channel.id,
                "guild": voice_channel.guild,
                "bitrate": voice_channel.bitrate,
                "user_limit": voice_channel.user_limit,
                "_state": voice_channel._state,
                "position": voice_channel.position,
                "_overwrites": voice_channel._overwrites,
                "category_id": voice_channel.category_id,
            },
            node=node_controller.get_best_node(voice_channel.guild),
            node_controller=node_controller,
        )


class NodeVoiceClient:
    def __init__(
        self,
        channel_id: int,
        guild_id: int,
        node: Node,
        node_controller: Controller,
    ):
        self.node: Node = node
        self.channel_id: int = channel_id
        self.guild_id: int = guild_id

        self._is_playing = False

        self._is_paused = False
        self._is_connected = True

        self.after_fn = None
        self.after_args = ()
        self.after_kwargs = {}
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.event_loop = asyncio.new_event_loop()

        self.node_controller: Controller = node_controller

    async def send_message(
        self,
        route: str,
        message: str,
        strict: bool = False,
        disconnect_extra: bool = False,
    ):
        if self.node not in self.node_controller.nodes.values():
            bot: commands.Bot = self.node_controller.parent.bot
            voice_channel: Optional[discord.VoiceChannel] = None
            for channel in bot.get_guild(self.guild_id).voice_channels:
                channel: discord.VoiceChannel
                if bot.user in channel.members:
                    voice_channel = channel
                    break

            if not voice_channel:
                return

            new_node: Node = self.node_controller.get_best_node(self.guild_id)

            self.node = new_node
            self.channel_id = voice_channel.id
            self._is_paused = False

            document = {
                "guild_id": self.guild_id,
                "voice_channel_id": self.channel_id,
                "reconnect": not disconnect_extra,
            }

            # connect to the channel now :D
            await self.node.client.request(
                "discord_connect", json.dumps(document), response=False
            )
            if strict:
                await self.after()
                return

        await self.node.client.request(route, message, response=False)

    def is_playing(self):
        return self._is_playing

    def is_paused(self):
        return self._is_paused

    def is_connected(self):
        return self._is_connected

    async def disconnect(self):
        document = {"guild_id": self.guild_id}
        await self.send_message(
            "discord_disconnect",
            json.dumps(document),
            strict=True,
            disconnect_extra=True,
        )

    async def stop(self):
        self._is_paused = False
        self._is_connected = False
        document = {"guild_id": self.guild_id}
        await self.send_message("discord_stop", json.dumps(document))

    async def play(self, song: Song, volume: int = 0.5):
        self._is_playing = True
        document = {
            "guild_id": song.guild_id,
            "stream": song.stream,
            "volume": volume,
            "codec": song.codec,
        }
        await self.send_message("discord_play", json.dumps(document))

    def set_after(self, fn, *args, **kwargs):
        self.after_fn = fn
        self.after_args = args
        self.after_kwargs = kwargs

    async def pause(self):
        document = {"guild_id": self.guild_id}
        self._is_paused = True
        await self.send_message(
            "discord_pause", json.dumps(document), strict=True
        )

    async def resume(self):
        document = {"guild_id": self.guild_id}
        self._is_paused = False
        await self.send_message(
            "discord_resume", json.dumps(document), strict=True
        )

    async def seek(
        self, song: Song, volume: int = 0.5, seconds_to_seek: int = 0
    ):
        if seconds_to_seek < 0:
            direction = "back"
        else:
            direction = "forward"
        document = {
            "guild_id": self.guild_id,
            "stream": song.stream,
            "volume": volume,
            "direction": direction,
            "seconds": abs(seconds_to_seek),
        }
        await self.send_message(
            "discord_seek", json.dumps(document), strict=True
        )

    async def set_volume(self, volume):
        document = {"guild_id": self.guild_id, "volume": volume}
        await self.send_message("discord_volume", json.dumps(document))

    async def after(self) -> asyncio.Future:
        self._is_playing = False
        if self.after_fn is not None:
            if inspect.iscoroutinefunction(self.after_fn):
                return asyncio.ensure_future(
                    self.after_fn(*self.after_args, **self.after_kwargs)
                )
            return asyncio.ensure_future(
                asyncio.get_event_loop().run_in_executor(
                    None, self.after_fn, self.after_args
                )
            )
