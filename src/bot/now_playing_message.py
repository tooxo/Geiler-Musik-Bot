"""
NowPlayingMessage
"""
import asyncio
import time
import traceback
import typing
from os import environ

import discord
import logging_manager
from discord.ext import commands

if typing.TYPE_CHECKING:
    from bot.discord_music import DiscordBot
    from bot.type.song import Song


class NowPlayingMessage:
    """
    NowPlayingMessage
    """

    REACTION_PAUSE: str = (
        "\N{BLACK RIGHT-POINTING TRIANGLE WITH DOUBLE VERTICAL BAR}"
    )
    REACTION_NEXT: str = "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}"

    def __init__(self, parent: "DiscordBot") -> None:
        self.parent: "DiscordBot" = parent
        self.message: typing.Optional[discord.Message] = None
        self.no_embed_mode = environ.get("USE_EMBEDS", "True") == "False"
        self._song: typing.Optional["Song"] = None

        self._title: typing.Optional[str] = None
        self.bytes_read: int = 0

        self._stop = False

        self._add_reaction_manager: typing.Optional[asyncio.Future] = None
        self._remove_reaction_manager: typing.Optional[asyncio.Future] = None
        self.ctx: typing.Optional[commands.Context] = None

    async def _validate_message(self) -> bool:
        """
        Check if the message is reusable
        :return:
        """
        if self.message:
            try:
                channel: discord.TextChannel = self.message.channel
                await channel.fetch_message(self.message.id)
                return channel.last_message.id == self.message.id
            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException,
                AttributeError,
            ):
                return False
        return False

    def calculate_recurrences(self) -> bool:
        """
        calculates if the message will update more than 75 times to
        stop on long songs
        :return: bool if too big
        """
        if hasattr(self._song, "duration"):
            recurrences = self._song.duration / 5
            if recurrences < 75:
                return True
        return False

    async def _delete_message(self) -> None:
        if self.message:
            try:
                await self.message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

    def _same_channel_check(self, user_id: int, guild_id: int) -> bool:
        try:
            return (
                self.parent.guilds[guild_id].voice_client.channel_id
                == self.parent.bot.get_guild(guild_id)
                .get_member(user_id)
                .voice.channel.id
            )
        except AttributeError:
            return False

    @staticmethod
    def _run_coroutine(coroutine: typing.Coroutine) -> typing.Any:
        asyncio.run_coroutine_threadsafe(coroutine, asyncio.get_event_loop())

    async def _add_reactions(self, ctx: commands.Context) -> bool:
        def _check(payload: discord.RawReactionActionEvent) -> bool:
            if not self.message:
                return False
            try:
                if (
                    payload.message_id == self.message.id
                    and self.parent.bot.user.id != payload.user_id
                    and self._same_channel_check(
                        user_id=payload.user_id, guild_id=payload.guild_id
                    )
                ):
                    voice_client = self.parent.guilds[ctx.guild.id].voice_client
                    if payload.emoji.name == self.REACTION_PAUSE:
                        if voice_client.is_paused():
                            self._run_coroutine(voice_client.resume())
                        else:
                            self._run_coroutine(voice_client.pause())
                    if payload.emoji.name == self.REACTION_NEXT:
                        self._run_coroutine(voice_client.stop())
                        self._stop = True
            except AttributeError:
                traceback.print_exc()
            return False

        if self.message:
            try:
                await self.message.add_reaction(emoji=self.REACTION_PAUSE)
                await self.message.add_reaction(emoji=self.REACTION_NEXT)
            except (
                discord.HTTPException,
                discord.Forbidden,
                discord.NotFound,
                discord.InvalidArgument,
            ):
                return False

        self._add_reaction_manager = asyncio.ensure_future(
            self.parent.bot.wait_for(
                "raw_reaction_add", timeout=None, check=_check
            )
        )
        self._remove_reaction_manager = asyncio.ensure_future(
            self.parent.bot.wait_for(
                "raw_reaction_remove", timeout=None, check=_check
            )
        )

        return True

    async def _update(self, ctx: commands.Context) -> None:
        if self._stop is True:
            return
        try:
            voice_client = self.parent.guilds[ctx.guild.id].voice_client
            if not voice_client.is_paused():
                now_time = round(self.bytes_read / 192000)
                finish_second = int(
                    self.parent.guilds[ctx.guild.id].now_playing.duration
                )
                description = (
                    "`"
                    + time.strftime("%H:%M:%S", time.gmtime(now_time))
                    + " / "
                    + time.strftime(
                        "%H:%M:%S",
                        time.gmtime(
                            self.parent.guilds[
                                ctx.guild.id
                            ].now_playing.duration
                        ),
                    )
                    + "`"
                )

                percentage = int((now_time / finish_second) * 100)

                if percentage > 100:
                    return
                count = percentage / 4
                hashes = ""
                while count > 0:
                    hashes += self.parent.guilds[ctx.guild.id].full
                    count -= 1
                while len(hashes) < 25:
                    hashes += self.parent.guilds[ctx.guild.id].empty
                hashes += " " + str(percentage) + "%"

                embed2 = discord.Embed(
                    title=self._title, color=0x00FFCC, url=self._song.link
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
                    while voice_client.is_paused():
                        await asyncio.sleep(0.1)
                    await self._update(ctx=ctx)
        except (
            TypeError,
            AttributeError,
            discord.HTTPException,
            RecursionError,
        ) as thrown_exception:
            self.parent.log.warning(
                logging_manager.debug_info(thrown_exception)
            )
            return
        await asyncio.sleep(5)
        if self._stop is False:
            await self._update(ctx=ctx)

    async def new_song(
        self, ctx: typing.Optional[commands.Context] = None
    ) -> None:
        """
        This gets called, when a new song gets started.
        :return:
        """
        if ctx:
            self.ctx = ctx
        else:
            ctx = self.ctx
        self._song = self.parent.guilds[ctx.guild.id].now_playing
        self._stop = False
        if (
            not self._song.title or self._song.title == "YouTube"
        ):  # fix for a py_tube bug
            title = "`" + self._song.term + "`"
        else:
            title = "`" + self._song.title + "`"
        self._title = title
        embed: discord.Embed = discord.Embed(
            title=title, colour=0x00FFCC, url=self._song.link
        )
        embed.set_author(name="Currently Playing:")
        if self.calculate_recurrences():
            embed.add_field(
                name=self.parent.guilds[ctx.guild.id].empty * 25, value=" 0%"
            )
        if await self._validate_message():
            if self.no_embed_mode:
                await self.message.edit(content=title)
            else:
                await self.message.edit(embed=embed)
        else:
            await self._delete_message()
            if self.no_embed_mode:
                self.message: discord.Message = await ctx.send(content=title)
            else:
                self.message: discord.Message = await ctx.send(embed=embed)
        if not self.no_embed_mode:
            if self.calculate_recurrences():
                asyncio.ensure_future(self._update(ctx=ctx))
            await self._add_reactions(ctx=ctx)

    async def after_song(
        self,
        ctx: typing.Optional[commands.Context] = None,
        guild_id: typing.Optional[int] = None,
    ) -> None:
        """
        This gets called after a song is finished.
        :return:
        """
        # noinspection PyBroadException
        if ctx:
            self.ctx = ctx
            guild_id = ctx.guild.id
        try:
            self._stop = True
            self._song = None
            self.bytes_read = 0
            if self._add_reaction_manager:
                if not self._add_reaction_manager.cancelled():
                    self._add_reaction_manager.cancel()
            if self._remove_reaction_manager:
                if not self._remove_reaction_manager.cancelled():
                    self._remove_reaction_manager.cancel()
            if (
                len(self.parent.guilds[guild_id].song_queue.queue) == 0
                or not self.parent.guilds[guild_id].voice_client
            ):
                await self._delete_message()
        except Exception:
            print(traceback.format_exc())
