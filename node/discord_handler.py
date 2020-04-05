"""
DiscordHandler
"""
import asyncio
import json
import logging
import re
import traceback
from typing import Dict, Optional, Union

from karp.client import KARPClient

import av_audio_source
import discord
from discord.ext import commands


class Guild:
    """
    Guild
    """

    def __init__(self) -> None:
        self.updater: Optional[asyncio.Future] = None


class DiscordHandler:
    """
    DiscordHandler
    """

    def __init__(self, api_key, client: KARPClient, node):
        self.__api_key = api_key

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.bot: commands.Bot = commands.Bot(
            command_prefix=api_key,
            fetch_offline_members=False,
            guild_subscriptions=False,
            loop=asyncio.get_event_loop(),
        )
        self.guilds: Dict[int, Guild] = {}

        self.client: KARPClient = client

        self.node = node

        self.started = asyncio.Event()

        logging.getLogger("discord").setLevel(logging.INFO)

        @self.bot.event
        async def on_message(message: discord.Message) -> discord.Message:
            """
            Fires on Message
            :param message:
            :return:
            """
            # no commands should be accepted
            return message

        @self.bot.event
        async def on_error(event, *args, **kwargs) -> None:
            """
            Fires on error
            :param event:
            :param args:
            :param kwargs:
            :return:
            """
            print(traceback.format_exc(event))
            print(event, *args, **kwargs)

        # noinspection PyUnusedLocal
        @self.bot.event
        async def on_ready(*args) -> None:  # pylint: disable=unused-argument
            """
            Fires on ready
            :param args:
            :return:
            """
            print("Startup Complete.")
            self.started.set()

    @staticmethod
    def validate_token(token: str) -> bool:
        """
        Validate DPY Token
        :param token: token
        :return:
        """
        pattern = r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}"
        return re.match(pattern, token) is not None

    async def update_state(self, guild_id: int) -> None:
        """
        Update the main client with the current bytes read
        :param guild_id: guild_id
        :return:
        """
        voice_client: discord.VoiceClient = self.bot.get_guild(
            guild_id
        ).voice_client
        source: av_audio_source.AvAudioSource = voice_client.source
        while voice_client.is_playing() or voice_client.is_paused():
            await asyncio.sleep(2)
            if not voice_client.is_paused():
                document = {
                    "guild_id": guild_id,
                    "bytes_read": source.bytes_read,
                }
                await self.client.request(
                    "discord_bytes", json.dumps(document), response=False
                )

    async def stop(self) -> None:
        """
        Stop the discord bot
        :return:
        """
        return await self.bot.close()

    async def start(self) -> None:
        """
        Start the bot.
        :return:
        """
        print("Starting the bot.")
        try:
            await self.bot.start(self.__api_key)
        except SystemExit:
            await self.bot.logout()

    def after(self, error, guild_id: int) -> None:
        """
        Run after a song is finished
        :param error:
        :param guild_id:
        :return:
        """
        if error:
            print("play_error", traceback.format_exc(error))
        document = {
            "guild_id": guild_id,
            "connected": self.bot.get_guild(
                guild_id
            ).voice_client.is_connected(),
        }
        asyncio.new_event_loop().run_until_complete(
            self.client.request(
                "discord_after", json.dumps(document), None, False
            )
        )
        if self.guilds[guild_id].updater:
            self.guilds[guild_id].updater.cancel()

    async def connect(self, data) -> None:
        """
        Connect to a channel
        :param data:
        :return:
        """
        # guild_id, voice_channel_id, reconnect
        data = json.loads(data)
        channel: discord.VoiceChannel = self.bot.get_channel(
            data["voice_channel_id"]
        )

        # reconnect routine
        # it needs to connect and disconnect again to update the voice state
        # so audio can be sent again
        if channel.guild.id not in self.guilds:
            for chan in self.bot.get_guild(channel.guild.id).voice_channels:
                if self.bot.user in chan.members:
                    try:
                        _temporary_voice_client = await channel.connect(
                            timeout=5, reconnect=False
                        )
                        await _temporary_voice_client.disconnect(force=True)
                    except Exception as thrown_exception:
                        print(thrown_exception)
                    break

        if not data["reconnect"]:
            return

        await channel.connect()
        self.guilds[channel.guild.id] = Guild()

    async def disconnect(self, data) -> None:
        """
        Disconnect from channel
        :param data:
        :return:
        """
        # guild_id
        data = json.loads(data)
        # self.bot.get_guild(data["guild_id"]).voice_client.stop()
        await self.bot.get_guild(data["guild_id"]).voice_client.disconnect()

    async def play(self, data) -> None:
        """
        Play a song
        :param data:
        :return:
        """
        # guild_id, stream, volume, codec
        data = json.loads(data)
        new_stream, before_args, player = (
            data["stream"],
            "",
            av_audio_source.AvAudioSource,
        )
        self.bot.get_guild(data["guild_id"]).voice_client.play(
            source=player(
                source=new_stream,
                volume=data["volume"],
                before_options=before_args,
            ),
            after=lambda err: self.after(err, data["guild_id"]),
        )
        self.guilds[data["guild_id"]].updater = asyncio.ensure_future(
            self.update_state(data["guild_id"])
        )

    async def seek(self, data: str) -> None:
        """
        Seek forwards or backwards
        :param data:
        :return:
        """
        # guild_id, stream, volume, seconds, direction
        parsed_data: Dict[str, Union[str, int]] = json.loads(data)

        voice_client: discord.VoiceClient = self.bot.get_guild(
            parsed_data["guild_id"]
        ).voice_client

        if isinstance(voice_client.source, av_audio_source.AvAudioSource):
            if parsed_data["direction"] == "back":
                parsed_data["seconds"] *= -1
            voice_client.source.seek(parsed_data["seconds"])
            document = {
                "guild_id": parsed_data["guild_id"],
                "bytes_read": voice_client.source.bytes_read,
            }
            await self.client.request(
                "discord_bytes", json.dumps(document), response=False
            )
        else:
            raise NotImplementedError

    def skip(self, data) -> None:
        """
        Skip a song
        :param data:
        :return:
        """
        # guild_id
        data = json.loads(data)
        voice_client: discord.VoiceClient = self.bot.get_guild(
            data["guild_id"]
        ).voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()

    def volume(self, data) -> None:
        """
        Change the volume
        :param data:
        :return:
        """
        # guild_id, volume
        data = json.loads(data)
        self.bot.get_guild(data["guild_id"]).voice_client.source.set_volume(
            data["volume"]
        )

    def pause(self, data: str) -> None:
        """
        Pause the player
        :param data:
        :return:
        """
        # guild_id
        data = json.loads(data)
        self.bot.get_guild(data["guild_id"]).voice_client.pause()

    def resume(self, data) -> None:
        """
        Resume the playback
        :param data:
        :return:
        """
        # guild_id
        data = json.loads(data)
        self.bot.get_guild(data["guild_id"]).voice_client.resume()
