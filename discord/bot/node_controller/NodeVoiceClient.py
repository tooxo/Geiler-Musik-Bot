import asyncio
import inspect
import json
from concurrent.futures import ThreadPoolExecutor

import discord
from bot.node_controller.controller import Controller, Node
from bot.type.song import Song


class NodeVoiceClient:
    def __init__(self, channel_id: int, guild_id: int, node: Node):
        self.node: Node = node
        self.channel_id: int = channel_id
        self.guild_id: int = guild_id
        self._is_playing = False

        self._is_paused = False

        self.source = None
        self.after_fn = None
        self.after_args = ()
        self.after_kwargs = {}
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.event_loop = asyncio.new_event_loop()

    def is_playing(self):
        return self._is_playing

    def is_paused(self):
        return self._is_paused

    async def disconnect(self):
        document = {"guild_id": self.guild_id}
        self.node.writer.write(f"C_DCON_{json.dumps(document)}".encode())
        await self.node.writer.drain()

    def stop(self):
        self._is_paused = False
        document = {"guild_id": self.guild_id}
        self.node.writer.write(f"C_STOP_{json.dumps(document)}".encode())
        asyncio.ensure_future(self.node.writer.drain())

    def play(self, song: Song, volume: int = 0.5):
        self._is_playing = True
        document = {
            "guild_id": song.guild_id,
            "stream": song.stream,
            "volume": volume,
            "youtube_stream": song.youtube_stream,
            "cipher": song.cipher,
        }
        self.node.writer.write(f"C_PLAY_{json.dumps(document)}".encode())
        asyncio.ensure_future(self.node.writer.drain())

    def set_after(self, fn, *args, **kwargs):
        self.after_fn = fn
        self.after_args = args
        self.after_kwargs = kwargs

    def pause(self):
        document = {"guild_id": self.guild_id}
        self._is_paused = True
        self.node.writer.write(f"C_PAUS_{json.dumps(document)}".encode())
        asyncio.ensure_future(self.node.writer.drain())

    def resume(self):
        document = {"guild_id": self.guild_id}
        self._is_paused = False
        self.node.writer.write(f"C_UNPA_{json.dumps(document)}".encode())
        asyncio.ensure_future(self.node.writer.drain())

    def set_volume(self, volume):
        document = {"guild_id": self.guild_id, "volume": volume}
        self.node.writer.write(f"C_VOLU_{json.dumps(document)}".encode())
        asyncio.ensure_future(self.node.writer.drain())

    def after(self):
        self._is_playing = False
        if self.after_fn is not None:
            if inspect.iscoroutinefunction(self.after_fn):
                return asyncio.ensure_future(
                    self.after_fn(*self.after_args, **self.after_kwargs)
                )
            else:
                return asyncio.ensure_future(
                    asyncio.get_event_loop().run_in_executor(
                        None, self.after_fn, self.after_args
                    )
                )


class NodeVoiceChannel(discord.VoiceChannel):
    def __init__(self, *, state, guild, data, node: Node):
        super().__init__(state=state, guild=guild, data=data)
        self.node: Node = node

    async def connect(self, *, timeout=60.0, reconnect=True):
        document = {"guild_id": self.guild.id, "voice_channel_id": self.id}
        self.node.writer.write(f"C_CONN_{json.dumps(document)}".encode())
        await self.node.writer.drain()
        return NodeVoiceClient(self.id, self.guild.id, self.node)

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
        )
