"""
New (improved) Player
"""
import asyncio
import random
import re

import discord
from discord.ext import commands
from typing import TYPE_CHECKING, Dict, List

import logging_manager
from bot.type.guild import Guild
from bot.type.url import Url
from bot.node_controller.node_voice_client import NodeVoiceChannel
from bot.now_playing_message import NowPlayingMessage
from bot.type.exceptions import (
    NoResultsFound,
    SongExtractionException,
    BasicError,
    NoNodeReadyException,
)
from bot.type.song import Song
from bot.type.variable_store import VariableStore
from bot.voice.checks import Checks

if TYPE_CHECKING:
    from bot.discord_music import DiscordBot


class BetaPlayer(commands.Cog):
    """
    New (improved) Player
    """

    def __init__(self, _bot: commands.Bot, _parent: "DiscordBot"):
        self.bot = _bot
        self.parent = _parent
        self.guilds: Dict[int, Guild] = _parent.guilds

    async def play_check(self, ctx: commands.Context, url: str) -> bool:
        """
        Checks if a url or term is supported by the bots architecture.
        @param ctx:
        @param url:
        @return:
        """
        if not await self.join_check(ctx):
            return False
        if not await self.join_channel(ctx=ctx):
            return False

        if PlayerHelper.determine_content_type(
                url) is not None or url.lower() == "charts":
            return True
        if re.match(VariableStore.url_pattern, url) is not None:
            await self.parent.send_error_message(
                ctx, "This is not a valid/supported url."
            )
            return False
        return True

    async def join_check(self, ctx: commands.Context) -> bool:
        """
        Checks if the bot is able to join the users voice channel
        @param ctx:
        @return:
        """
        if self.guilds[ctx.guild.id].voice_channel is None:
            state: discord.VoiceState = ctx.author.voice
            if ctx.author.voice is not None:
                if len(state.channel.members) >= state.channel.user_limit != 0:
                    await self.parent.send_error_message(
                        ctx=ctx, message="Your channel is full."
                    )
                    return False
                self.guilds[
                    ctx.guild.id
                ].voice_channel = ctx.author.voice.channel
            else:
                await self.parent.send_error_message(
                    ctx, "You need to be in a channel."
                )
                return False
        return True

    # Discord Commands
    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["p"])
    async def play(self, ctx, *, content: str):
        if not await self.play_check(ctx, content):
            return
        return await self._add_to_queue(content, ctx)

    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["ps", "playskip"])
    async def play_skip(self, ctx, *, content: str):
        if not await self.play_check(ctx, content):
            return
        return await self._add_to_queue(content, ctx, skip=True)

    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["pn", "playnext"])
    async def play_next(self, ctx, *, content: str):
        if not await self.play_check(ctx, content):
            return
        return await self._add_to_queue(content, ctx, priority=True)

    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["sp"])
    async def play_shuffle(self, ctx, *, content: str):
        if not await self.play_check(ctx, content):
            return
        return await self._add_to_queue(content, ctx, shuffle=True)

    @play.error
    @play_skip.error
    @play_next.error
    @play_shuffle.error
    async def _play_error(self, ctx, error):
        if self.guilds[ctx.guild.id].job_lock.locked():
            self.guilds[ctx.guild.id].job_lock.release()
        raise error

    @commands.command()
    @commands.check(Checks.user_connection_check)
    async def connect(self, ctx):
        was_connected = self.guilds[ctx.guild.id].voice_client is not None
        if not await self.join_channel(ctx=ctx):
            return
        if was_connected:
            return await self.parent.send_error_message(
                ctx, "Already Connected."
            )
        return await self.parent.send_embed_message(ctx, "Connected.")

    @commands.command()
    async def join_channel(self, ctx: commands.Context) -> bool:
        """
        Joins a channel
        @param ctx:
        @return: returns if the join process was successful
        """
        if self.guilds[ctx.guild.id].voice_client is None:
            try:
                if (
                        ctx.author.voice.channel.user_limit
                        <= len(ctx.author.voice.channel.members)
                        and ctx.author.voice.channel.user_limit != 0
                ):
                    if ctx.guild.me.guild_permissions.administrator is False:
                        await self.parent.send_embed_message(
                            ctx,
                            "Error while joining your channel. :frowning: (1)",
                        )
                        return False
                else:
                    self.guilds[
                        ctx.guild.id
                    ].voice_client = await NodeVoiceChannel.from_channel(
                        ctx.author.voice.channel, self.parent.node_controller
                    ).connect()
                    self.guilds[
                        ctx.guild.id
                    ].now_playing_message = NowPlayingMessage(self.parent)
            except (TimeoutError,) as discord_error:
                self.parent.log.warning(
                    logging_manager.debug_info(
                        "channel_join " + str(discord_error)
                    )
                )
                self.guilds[ctx.guild.id].voice_channel = None
                await self.parent.send_embed_message(
                    ctx, "Error while joining your channel. :frowning: (2)"
                )
                return False
            except NoNodeReadyException as no_node_ready_exception:
                await self.parent.send_error_message(
                    ctx, str(no_node_ready_exception)
                )
                return False
        return True

    # Queue Related
    async def _add_to_queue(
            self,
            content: str,
            ctx: commands.Context,
            skip: bool = False,
            priority: bool = False,
            shuffle: bool = False,
    ):
        await self.guilds[ctx.guild.id].job_lock.acquire()
        if not self.guilds[ctx.guild.id].voice_client:
            self.guilds[ctx.guild.id].job_lock.release()
            return
        content_type = PlayerHelper.determine_content_type(content)
        try:
            song_list: List[Song] = await PlayerHelper.load_content_information(
                content, content_type, self.parent, ctx
            )
        except (asyncio.TimeoutError, NoResultsFound, SongExtractionException,
                BasicError) as be:
            print(be)
            if self.guilds[ctx.guild.id].job_lock.locked(): self.guilds[
                ctx.guild.id].job_lock.release()
            return
            # shuffle if requested
        if shuffle:
            random.shuffle(song_list)
        if skip:
            self.guilds[ctx.guild.id].song_queue.clear()
            await self.guilds[ctx.guild.id].voice_client.stop()
        # view message
        if self.guilds[ctx.guild.id].now_playing or len(song_list) > 1:
            if len(song_list) > 1:
                await self.parent.send_embed_message(
                    ctx,
                    f"Queued {len(song_list)} Track"
                    f"{'s' if len(song_list) > 1 else ''}.",
                )
            else:
                await self.parent.send_embed_message(
                    ctx,
                    f"Queued **"
                    f"{song_list[0].title or song_list[0].term or song_list[0].link}"
                    f"**."
                )
        # now add to queue
        if priority:
            self.guilds[ctx.guild.id].song_queue.queue.extendleft(song_list)
        else:
            self.guilds[ctx.guild.id].song_queue.queue.extend(song_list)
        if self.guilds[ctx.guild.id].job_lock.locked():
            self.guilds[ctx.guild.id].job_lock.release()
        for _ in song_list:
            await self._playback(ctx)

    async def _playback(self, ctx):
        """
        Start playback
        @param ctx:
        @return:
        """
        guild_id = ctx.guild.id
        guild = self.guilds[guild_id]
        if guild.song_queue.qsize():
            await guild.playback_lock.acquire()

            if not guild.voice_client or not guild.song_queue.qsize():
                return guild.playback_lock.release()
            song = await guild.song_queue.get()

            if not song.stream:
                try:
                    song = await PlayerHelper.complete_content_information(
                        song, self.parent, ctx
                    )
                except (
                        asyncio.TimeoutError,
                        NoResultsFound,
                        SongExtractionException,
                        BasicError,
                ):
                    if guild.job_lock.locked():
                        guild.job_lock.release()
                    return await self._playback(ctx)
            if not guild.voice_client:
                guild.job_lock.release() if guild.job_lock.locked() else None
                return
            guild.voice_client.set_after(self._after_song, ctx)
            await guild.voice_client.play(
                song, guild.volume
            )
            guild.now_playing = song
            if not guild.now_playing_message:
                guild.now_playing_message = NowPlayingMessage(
                    parent=self.parent)
            await self.guilds[guild_id].now_playing_message.new_song(ctx)

    async def _after_song(self, ctx) -> None:
        guild_id = ctx.guild.id
        await self.guilds[guild_id].now_playing_message.after_song(
            ctx, guild_id
        ) if self.guilds[guild_id].now_playing_message else None
        self.guilds[guild_id].now_playing = None
        if self.guilds[guild_id].playback_lock.locked():
            self.guilds[guild_id].playback_lock.release()
        # if self.guilds[guild_id].voice_client:
        #    await self._playback(ctx)


class PlayerHelper:
    """
    Functions to help the player
    """

    @staticmethod
    def determine_content_type(content: str):
        return Url.determine_source(content)

    @staticmethod
    async def load_content_information(
            content: str,
            content_type: int,
            parent: "DiscordBot",
            ctx: commands.Context,
    ) -> List[Song]:
        def _add_user(arg1: Song):
            arg1.user = ctx.message.author.id
            arg1.guild_id = ctx.guild.id
            return arg1

        song_list = []
        if content_type == Url.youtube:
            song_list = await PlayerHelper.load_content_information_youtube(
                content, parent
            )
        if content_type == Url.spotify:
            song_list = await PlayerHelper.load_content_information_spotify(
                content, parent
            )
        if content_type == Url.soundcloud:
            song_list = await PlayerHelper.load_content_information_soundcloud(
                content, parent
            )
        if content_type == Url.other:
            # song_list = await PlayerHelper.search(content, parent, ctx)
            song_list = [Song(term=content)]
        return list(map(_add_user, song_list))

    @staticmethod
    async def load_content_information_youtube(
            content: str, parent: "DiscordBot",
    ) -> List[Song]:
        youtube_type: int = Url.determine_youtube_type(content)
        if youtube_type == Url.youtube_url:
            return [Song(link=content)]
        else:
            return await parent.youtube.youtube_playlist(content)

    @staticmethod
    async def load_content_information_spotify(
            content: str, parent: "DiscordBot",
    ) -> List[Song]:
        spotify_type = Url.determine_spotify_type(content)
        if spotify_type == Url.spotify_track:
            return [await parent.spotify.spotify_track(content)]
        if spotify_type == Url.spotify_playlist:
            return await parent.spotify.spotify_playlist(content)
        if spotify_type == Url.spotify_artist:
            return await parent.spotify.spotify_artist(content)
        if spotify_type == Url.spotify_album:
            return await parent.spotify.spotify_album(content)
        return []

    @staticmethod
    async def load_content_information_soundcloud(
            content: str, parent: "DiscordBot"
    ) -> List[Song]:
        soundcloud_type = Url.determine_soundcloud_type(content)
        if soundcloud_type == Url.soundcloud_track:
            return [await parent.soundcloud.soundcloud_track(content)]
        else:
            return await parent.soundcloud.soundcloud_playlist(content)

    @staticmethod
    async def search(
            content: str, parent: "DiscordBot", ctx: commands.Context
    ) -> List[Song]:

        return [
            await parent.youtube.youtube_term(
                song=Song(term=content, guild_id=ctx.guild.id),
                service=parent.guilds[ctx.guild.id].service,
            )
        ]

    @staticmethod
    async def complete_content_information(
            song: Song, parent: "DiscordBot", ctx: commands.Context
    ):
        if song.link:
            if PlayerHelper.determine_content_type(song.link) == Url.youtube:
                return Song.copy_song(
                    await parent.youtube.youtube_url(url=song.link,
                                                     guild_id=song.guild_id),
                    song
                )
            else:
                return Song.copy_song(
                    await parent.soundcloud.soundcloud_track(url=song.link),
                    song,
                )
        if song.term or song.title:
            song = Song.copy_song(
                song,
                (await PlayerHelper.search(song.title or song.term, parent,
                                           ctx))[
                    0]
            )
            return await PlayerHelper.complete_content_information(
                song, parent, ctx
            )
