import asyncio
import json
import re
import traceback
from typing import Dict

import discord
import FFmpegPCMAudio
from discord.ext import commands


class Guild:
    def __init__(self, voice_client: discord.VoiceClient):
        self.voice_client: discord.voice_client = voice_client
        self.updater: asyncio.Future


class DiscordHandler:
    def __init__(
        self,
        api_key,
        writer: asyncio.StreamWriter,
        reader: asyncio.StreamReader,
        node,
    ):
        self.__api_key = api_key

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.bot: commands.Bot = commands.Bot(
            command_prefix=api_key,
            fetch_offline_members=False,
            guild_subscriptions=False,
            loop=asyncio.get_event_loop(),
        )
        self.guilds: Dict[int] = {}

        self.writer: asyncio.StreamWriter = writer
        self.reader: asyncio.StreamReader = reader

        self.node = node

        @self.bot.event
        async def on_message(ignored):
            # no commands should be accepted
            pass

        @self.bot.event
        async def on_error(event, *args, **kwargs):
            traceback.print_exc()
            print(event, *args, **kwargs)

        @self.bot.event
        async def on_ready(*args):
            print("Ready!")
            self.writer.write("D_READY".encode())
            asyncio.ensure_future(self.writer.drain())

    @staticmethod
    def validate_token(token: str) -> bool:
        pattern = r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}"
        return re.match(pattern, token) is not None

    @staticmethod
    def split_response(command: str) -> list:
        if command.count("C_") > 1:
            return command.split("C_")[1:]
        return [command]

    def decide_on_stream(self, data: dict):
        # if the cipher is identical, the extractor was the node playing
        # the cipher is also only inserted in youtube_extraction so
        # soundcloud tracks will return the original stream
        if self.node.youtube.cipher == data["cipher"]:
            return (
                data["youtube_stream"],
                "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3",
            )
        if "stream/youtube_video" in data["stream"]:
            return data["stream"], ""
        return (
            data["stream"],
            "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 3",
        )

    async def update_state(self, guild_id: int):
        voice_client: discord.VoiceClient = self.guilds[guild_id].voice_client
        source: FFmpegPCMAudio.FFmpegOpusAudioB = voice_client.source
        while voice_client.is_playing():
            await asyncio.sleep(2)
            if not voice_client.is_paused():
                document = {
                    "guild_id": guild_id,
                    "bytes_read": source.bytes_read,
                }
                self.writer.write(f"S_BR_{json.dumps(document)}".encode())
                await self.writer.drain()

    async def handle_command(self, command: str):
        _commands = self.split_response(command)
        for c in _commands:
            c = c[2:]
            data = c[5:]
            if c.startswith("PLAY"):
                self.play(data)
            elif c.startswith("STOP"):
                self.skip(data)
            elif c.startswith("CONN"):
                await self.connect(data=data)
            elif c.startswith("DCON"):
                await self.disconnect(data)
            elif c.startswith("VOLU"):
                self.volume(data)
            elif c.startswith("PAUS"):
                self.pause(data)
            elif c.startswith("UNPA"):
                self.resume(data)

    async def stop(self):
        return await self.bot.close()

    async def start(self):
        print("Starting the bot.")
        await self.bot.start(self.__api_key)
        # self.bot.run(self.__api_key, loop=asyncio.new_event_loop())
        print("Starting the bot is done")

    def after(self, error, guild_id: int):
        if error:
            print(error)
        document = {"guild_id": guild_id}
        self.writer.write(f"Z_{json.dumps(document)}".encode())
        asyncio.new_event_loop().run_until_complete(self.writer.drain())
        if self.guilds[guild_id].updater:
            self.guilds[guild_id].updater.cancel()

    async def connect(self, data):
        # guild_id, voice_channel_id
        data = json.loads(data)
        channel: discord.VoiceChannel = self.bot.get_channel(
            data["voice_channel_id"]
        )
        voice_channel = await channel.connect()
        self.guilds[channel.guild.id] = Guild(voice_channel)

    async def disconnect(self, data):
        # guild_id
        data = json.loads(data)
        await self.guilds[data["guild_id"]].voice_client.disconnect()

    def play(self, data):
        # guild_id, stream, volume, youtube_stream, cipher
        data = json.loads(data)
        new_stream, before_args = self.decide_on_stream(data)
        self.guilds[data["guild_id"]].voice_client.play(
            source=FFmpegPCMAudio.FFmpegOpusAudioB(
                new_stream, volume=data["volume"], before_options=before_args
            ),
            after=lambda err: self.after(err, data["guild_id"]),
        )
        self.guilds[data["guild_id"]].updater = asyncio.ensure_future(
            self.update_state(data["guild_id"])
        )

    def skip(self, data):
        # guild_id
        data = json.loads(data)
        if (
            self.guilds[data["guild_id"]].voice_client.is_playing()
            or self.guilds[data["guild_id"]].voice_client.is_paused()
        ):
            self.guilds[data["guild_id"]].voice_client.stop()

    def volume(self, data):
        # guild_id, volume
        data = json.loads(data)
        self.guilds[data["guild_id"]].voice_client.source.set_volume(
            data["volume"]
        )

    def pause(self, data: str):
        # guild_id
        data = json.loads(data)
        self.guilds[data["guild_id"]].voice_client.pause()

    def resume(self, data):
        # guild_id
        data = json.loads(data)
        self.guilds[data["guild_id"]].voice_client.resume()
