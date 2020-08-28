"""
Events
"""
import asyncio
import time
from typing import Dict

import async_timeout
from discord import Member, VoiceState
from discord.ext.commands import Bot, Cog

from bot.now_playing_message import NowPlayingMessage
from bot.type.guild import Guild
from bot.type.queue import Queue


class Events(Cog):
    """
    Events
    """

    def __init__(self, bot, parent) -> None:
        self.bot: Bot = bot
        self.parent = parent
        self.guilds: Dict[int, Guild] = parent.guilds

        @self.bot.event
        async def on_guild_join(guild) -> None:
            """
            Triggers if someone joins a guild and adds it to memory
            :param guild: the server joined
            :return:
            """
            self.parent.log.debug("Joined a new Guild! Hello, " + guild.name)
            self.guilds[guild.id] = Guild()
            await self.guilds[guild.id].inflate_from_mongo(
                self.parent.mongo, guild.id
            )

        @self.bot.event
        async def on_voice_state_update(
            member: Member, before: VoiceState, after: VoiceState
        ):
            """
            Check for user leaving or joining your channel.
            :param member: Member, which joined
            :param before: Channel before
            :param after: Channel after
            :return:
            """
            try:
                if before.channel is not None:
                    guild_id = before.channel.guild.id
                else:
                    guild_id = after.channel.guild.id

                if self.guilds[guild_id].voice_channel is None:
                    return
                if member == self.bot.user:
                    if (
                        not after.channel
                        and not self.bot.get_guild(guild_id).voice_client
                    ):
                        self.guilds[guild_id].voice_channel = None
                        if self.guilds[guild_id].voice_client:
                            await self.guilds[guild_id].voice_client.after()
                        self.guilds[guild_id].voice_client = None
                        if self.guilds[guild_id].now_playing_message:
                            await self.guilds[
                                guild_id
                            ].now_playing_message.after_song(guild_id=guild_id)
                            self.guilds[guild_id].now_playing_message = None
                        self.guilds[guild_id].song_queue = Queue()
                        if self.guilds[guild_id].job_lock.locked():
                            self.guilds[guild_id].job_lock.release()
                        return
                    if (
                        not before.channel
                        and self.bot.get_guild(guild_id).voice_client
                    ):
                        if not self.guilds[guild_id].now_playing_message:
                            self.guilds[
                                guild_id
                            ].now_playing_message = NowPlayingMessage(
                                self.parent
                            )
                    if after.channel:
                        # Keep track of channel movements.
                        self.guilds[guild_id].voice_channel = after.channel
                        if self.guilds[guild_id].voice_client:
                            self.guilds[
                                guild_id
                            ].voice_client.channel_id = after.channel.id
                if (
                    self.guilds[guild_id].voice_channel is before.channel
                    and self.guilds[guild_id].voice_channel is not after.channel
                ):
                    if len(before.channel.members) == 1:
                        asyncio.ensure_future(
                            self.check_my_channel(before.channel, guild_id)
                        )
            except KeyError:
                pass

    async def check_my_channel(self, channel, guild_id) -> None:
        """
        Asynchronous function, checking if a bot is alone in a channel
        :param channel:
        :param guild_id:
        :return:
        """
        try:
            with async_timeout.timeout(300):
                while 1:
                    await asyncio.sleep(2)
                    if self.guilds[guild_id].voice_channel is not channel:
                        return
                    if len(self.guilds[guild_id].voice_channel.members) > 1:
                        return
                    if time.time() == 0:
                        break
        except asyncio.TimeoutError:
            if self.guilds[guild_id].voice_client is not None:
                # await self.guilds[guild_id].voice_client.disconnect()
                self.guilds[guild_id].song_queue.clear()
                await self.guilds[guild_id].voice_client.stop()
