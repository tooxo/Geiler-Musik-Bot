import asyncio
import time
from os import environ
from typing import Optional

import aiohttp

import discord
import logging_manager
from bot.node_controller.NodeVoiceClient import NodeVoiceClient


class NowPlayingMessage:
    def __init__(
        self,
        ctx,
        song=None,
        full=None,
        empty=None,
        discord_music=None,
        voice_client: NodeVoiceClient = None,
    ):
        self.discord_music = discord_music
        self.log = logging_manager.LoggingManager()
        self.song = song
        self._stop = False
        self.ctx = ctx
        self.full = full
        self.empty = empty
        self.message: Optional[discord.message.Message] = None
        if voice_client is not None:
            self.voice_client: NodeVoiceClient = voice_client
        if self.song is not None:
            if self.song.title == "_" or self.song.title is None:
                self.title = "`" + self.song.term + "`"
            else:
                self.title = "`" + self.song.title + "`"
        self.no_embed_mode = environ.get("USE_EMBEDS", "True") == "False"
        self.add_subroutine: (None, asyncio.Future) = None
        self.remove_subroutine: (None, asyncio.Future) = None
        self.bytes_read = 0

    def calculate_recurrences(self):
        """
        calculates if the message will update more than 75 times to stop on long songs
        :return: bool if too big
        """
        if hasattr(self.song, "duration"):
            recurrences = self.song.duration / 5
            if recurrences < 75:
                return True
        return False

    async def send(self):
        if self.song is None:
            return
        if not self.no_embed_mode:
            if self.calculate_recurrences():
                embed = discord.Embed(
                    title=self.title, color=0x00FFCC, url=self.song.link
                )
                embed.set_author(name="Currently Playing:")
                embed.add_field(name="░░░░░░░░░░░░░░░░░░░░░░░░░", value=" 0%")
                self.message = await self.ctx.send(embed=embed)
                asyncio.ensure_future(self.update())
            else:
                embed = discord.Embed(
                    title=self.title, color=0x00FFCC, url=self.song.link
                )
                embed.set_author(name="Currently Playing:")
                self.message = await self.ctx.send(embed=embed)
            await self.message.add_reaction(
                "\N{BLACK RIGHT-POINTING TRIANGLE WITH DOUBLE VERTICAL BAR}"
                # pause play
            )
            await self.message.add_reaction(
                "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}"
                # fast forward
            )
            await self.reaction_waiter()
        else:
            try:
                self.message = await self.ctx.send(content=self.title)
            except discord.errors.NotFound as p:
                self.log.warning(logging_manager.debug_info(p))

    async def update(self):
        if self._stop is True:
            return
        try:
            if not (self.voice_client.is_paused()):
                now_time = round(self.bytes_read / 192000)
                finish_second = int(
                    self.discord_music.guilds[
                        self.ctx.guild.id
                    ].now_playing.duration
                )
                description = (
                    "`"
                    + time.strftime("%H:%M:%S", time.gmtime(now_time))
                    + " / "
                    + time.strftime(
                        "%H:%M:%S",
                        time.gmtime(
                            self.discord_music.guilds[
                                self.ctx.guild.id
                            ].now_playing.duration
                        ),
                    )
                    + "`"
                )

                percentage = int((now_time / finish_second) * 100)

                if percentage > 100:
                    await self.stop()
                    return
                count = percentage / 4
                hashes = ""
                while count > 0:
                    hashes += self.full
                    count -= 1
                while len(hashes) < 25:
                    hashes += self.empty
                hashes += " " + str(percentage) + "%"

                embed2 = discord.Embed(
                    title=self.title, color=0x00FFCC, url=self.song.link
                )
                embed2.set_author(
                    name="Currently Playing:",
                    icon_url="https://i.imgur.com/dbS6H3k.gif",
                )
                embed2.add_field(name=hashes, value=description)
                try:
                    await self.message.edit(embed=embed2)
                except (discord.NotFound, TypeError):
                    return
            else:
                if self._stop is False:
                    while self.voice_client.is_paused():
                        await asyncio.sleep(0.1)
                    await self.update()
        except (
            TypeError,
            AttributeError,
            aiohttp.ServerDisconnectedError,
            RecursionError,
        ) as e:
            self.log.warning(logging_manager.debug_info(e))
            return
        await asyncio.sleep(5)
        if self._stop is False:
            await self.update()

    async def reaction_waiter(self):
        def same_channel_check(user: discord.Member):
            if hasattr(user, "voice"):
                if hasattr(user.voice, "channel"):
                    if self.voice_client.channel_id == user.voice.channel.id:
                        return True
            return False

        def run_coroutine(coroutine):
            asyncio.run_coroutine_threadsafe(
                coroutine, asyncio.get_event_loop()
            )

        def check_add(reaction: discord.Reaction, user: discord.Member):
            if reaction.message.id == self.message.id:
                if self.discord_music.bot.user.id != user.id:
                    if same_channel_check(user=user):
                        if (
                            reaction.emoji
                            == "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}"
                        ):
                            run_coroutine(self.voice_client.stop())
                            self._stop = True
                            return True
                        if (
                            reaction.emoji
                            == "\N{BLACK RIGHT-POINTING TRIANGLE WITH DOUBLE VERTICAL BAR}"
                        ):
                            try:
                                if self.voice_client.is_paused():
                                    run_coroutine(self.voice_client.resume())
                                else:
                                    run_coroutine(self.voice_client.pause())
                            except AttributeError as ae:
                                self.log.warning(logging_manager.debug_info(ae))
                return False

        def check_remove(reaction: discord.Reaction, user: discord.Member):
            if reaction.message.id == self.message.id:
                if self.discord_music.bot.user.id != user.id:
                    if same_channel_check(user=user):
                        if (
                            reaction.emoji
                            == "\N{BLACK RIGHT-POINTING TRIANGLE WITH DOUBLE VERTICAL BAR}"
                        ):
                            try:
                                if self.voice_client.is_paused():
                                    run_coroutine(self.voice_client.resume())
                                else:
                                    run_coroutine(self.voice_client.pause())
                            except AttributeError as ae:
                                self.log.warning(logging_manager.debug_info(ae))
                return False

        self.add_subroutine = asyncio.ensure_future(
            self.discord_music.bot.wait_for(
                "reaction_add", timeout=None, check=check_add
            )
        )
        self.remove_subroutine = asyncio.ensure_future(
            self.discord_music.bot.wait_for(
                "reaction_remove", timeout=None, check=check_remove
            )
        )

    async def stop(self):
        self._stop = True
        if self.song is None:
            await self.discord_music.delete_message(message=self.message)
            return
        if not self.no_embed_mode:
            try:
                await self.discord_music.delete_message(self.message)
                self.remove_subroutine.cancel()
                self.add_subroutine.cancel()
            except (AttributeError, discord.NotFound):
                pass
        else:
            await self.discord_music.delete_message(self.message)
