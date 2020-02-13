import asyncio
import time

import async_timeout

from bot.type.guild import Guild
from bot.type.queue import Queue
from discord.ext.commands import Cog


class Events(Cog):
    def __init__(self, bot, parent):
        self.bot = bot
        self.parent = parent

        @self.bot.event
        async def on_guild_join(guild):
            """
            Triggers if someone joins a guild and adds it to memory
            :param guild: the server joined
            :return:
            """
            self.parent.log.debug("Joined a new Guild! Hello, " + guild.name)
            self.parent.guilds[guild.id] = Guild()

        @self.bot.event
        async def on_voice_state_update(member, before, after):
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

                if self.parent.guilds[guild_id].voice_channel is None:
                    return
                if member is self.bot.user:
                    if self.bot.get_guild(guild_id).voice_client is not None:
                        self.parent.guilds[guild_id].voice_channel = None
                        self.parent.guilds[guild_id].voice_client = None
                        return

                if (
                    self.parent.guilds[guild_id].voice_channel is before.channel
                    and self.parent.guilds[guild_id].voice_channel
                    is not after.channel
                ):
                    if len(before.channel.members) == 1:
                        asyncio.ensure_future(
                            self.check_my_channel(before.channel, guild_id)
                        )
            except KeyError:
                pass

    async def check_my_channel(self, channel, guild_id):
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
                    if (
                        self.parent.guilds[guild_id].voice_channel
                        is not channel
                    ):
                        return
                    if (
                        len(self.parent.guilds[guild_id].voice_channel.members)
                        > 1
                    ):
                        return
                    if time.time() == 0:
                        break
        except asyncio.TimeoutError:
            if self.parent.guilds[guild_id].voice_client is not None:
                # await self.guilds[guild_id].voice_client.disconnect()
                self.parent.guilds[guild_id].song_queue = Queue()
                self.parent.guilds[guild_id].voice_client.stop()
