import asyncio
import re
import traceback
from os import environ

import discord
import logging_manager
from bot.FFmpegPCMAudio import FFmpegPCMAudioB, PCMVolumeTransformerB
from bot.now_playing_message import NowPlayingMessage
from bot.type.error import Error
from bot.type.errors import Errors
from bot.type.queue import Queue
from bot.type.song import Song
from bot.type.spotify_type import SpotifyType
from bot.type.variable_store import VariableStore
from bot.type.youtube_type import YouTubeType
from bot.type.url import Url
from discord.ext import commands
from discord.ext.commands import Cog


class Player(Cog):
    def __init__(self, bot, parent):
        self.bot = bot
        self.parent = parent

    async def pre_player(self, ctx, bypass=None):
        if (
            self.parent.dictionary[ctx.guild.id].song_queue.qsize() > 0
            or bypass is not None
        ):
            if bypass is None:
                small_dict = await self.parent.dictionary[ctx.guild.id].song_queue.get()
            else:
                small_dict = bypass
            self.parent.dictionary[
                ctx.guild.id
            ].now_playing_message = NowPlayingMessage(
                message=await self.parent.send_embed_message(
                    ctx=ctx, message=" Loading ... "
                ),
                ctx=ctx,
            )
            if small_dict.stream is None:
                if small_dict.link is not None:
                    # url
                    youtube_dict = await self.parent.youtube.youtube_url(
                        small_dict.link
                    )
                else:
                    if small_dict.title is None:
                        self.parent.log.warning(small_dict)
                    # term
                    youtube_dict = await self.parent.youtube.youtube_term(
                        small_dict.title
                    )
                    # youtube_dict = await self.parent.youtube_t.youtube_term(small_dict['title'])
                if isinstance(youtube_dict, Error):
                    if youtube_dict.reason != Errors.error_please_retry:
                        await self.parent.send_error_message(ctx, youtube_dict.reason)
                        await self.parent.dictionary[
                            ctx.guild.id
                        ].now_playing_message.delete()
                        await self.pre_player(ctx)
                        return
                    await self.parent.dictionary[
                        ctx.guild.id
                    ].now_playing_message.delete()
                    await self.pre_player(ctx, bypass=small_dict)
                    return
                youtube_dict.user = small_dict.user
                youtube_dict.image_url = small_dict.image_url
                await self.player(ctx, youtube_dict)
            else:
                await self.player(ctx, small_dict)

            asyncio.ensure_future(self.preload_song(ctx=ctx))

    async def extract_infos(self, url, ctx):
        url_type = Url.determine_source(url=url)
        if url_type == Url.youtube:
            return await self.extract_first_infos_youtube(url=url, ctx=ctx)
        elif url_type == Url.spotify:
            return await self.extract_first_infos_spotify(url=url, ctx=ctx)
        else:
            return await self.extract_first_infos_other(url=url, ctx=ctx)

    async def extract_first_infos_youtube(self, url, ctx):
        youtube_type = Url.determine_youtube_type(url=url)
        if youtube_type == Url.youtube_url:
            __song = Song()
            __song.user = ctx.message.author
            __song.link = url
            return [__song]
        elif youtube_type == Url.youtube_playlist:
            __songs = []
            __song_list = await self.parent.youtube.youtube_playlist(url)
            if len(__song_list) == 0:
                await self.parent.send_error_message(ctx, Errors.spotify_pull)
                return []
            for track in __song_list:
                track.user = ctx.message.author
                __songs.append(track)
            return __songs

    async def extract_first_infos_spotify(self, url, ctx):
        spotify_type = Url.determine_spotify_type(url=url)
        __songs = []
        __song = Song()
        __song.user = ctx.message.author
        if spotify_type == Url.spotify_playlist:
            __song_list = await self.parent.spotify.spotify_playlist(url)
            if len(__song_list) == 0:
                await self.parent.send_error_message(
                    ctx=ctx, message=Errors.spotify_pull
                )
                return []
            for track in __song_list:
                __song = Song(song=__song)
                __song.title = track
                __songs.append(__song)
            return __songs
        elif spotify_type == Url.spotify_track:
            track = await self.parent.spotify.spotify_track(url)
            if track is not None:
                __song.title = track.title
                __song.image_url = track.image_url
                return [__song]
            else:
                return []
        elif spotify_type == Url.spotify_artist:
            song_list = await self.parent.spotify.spotify_artist(url)
            for track in song_list:
                __song = Song(song=__song)
                __song.title = track
                __songs.append(__song)
            return __songs
        elif spotify_type == Url.spotify_album:
            song_list = await self.parent.spotify.spotify_album(url)
            for track in song_list:
                __song = Song(song=__song)
                __song.title = track
                __songs.append(__song)
            return __songs

    async def extract_first_infos_other(self, url, ctx):
        if url == "charts":
            __songs = []
            __song = Song()
            __song.user = ctx.message.author
            song_list = await self.parent.spotify.spotify_playlist(
                "https://open.spotify.com/playlist/37i9dQZEVXbMDoHDwVN2tF?si=vgYiEOfYTL-ejBdn0A_E2g"
            )
            for track in song_list:
                song = Song(song=__song)
                song.title = track
                __songs.append(song)
            return __songs
        else:
            __song = Song()
            __song.title = url
            __song.user = ctx.message.author
            return [__song]

    async def add_to_queue(self, url, ctx, first_index_push=False, playskip=False):
        if playskip:
            self.parent.dictionary[ctx.guild.id].song_queue = Queue()

        songs = await self.extract_infos(url=url, ctx=ctx)
        if len(songs) > 1:
            self.parent.dictionary[ctx.guild.id].song_queue.queue.extend(songs)
            await self.parent.send_embed_message(
                ctx=ctx,
                message=":asterisk: Added "
                + str(len(songs))
                + " Tracks to Queue. :asterisk:",
            )
        elif len(songs) == 1:
            if first_index_push:
                self.parent.dictionary[ctx.guild.id].song_queue.queue.extendleft(songs)
            else:
                self.parent.dictionary[ctx.guild.id].song_queue.queue.extend(songs)
            title = ""
            if songs[0].title is not None:
                title = songs[0].title
            else:
                try:
                    title = songs[0].link
                except AttributeError:
                    pass
            if self.parent.dictionary[ctx.guild.id].voice_client.is_playing():
                if not playskip:
                    await self.parent.send_embed_message(
                        ctx, ":asterisk: Added **" + title + "** to Queue."
                    )

        try:
            if playskip:
                if self.parent.dictionary[ctx.guild.id].voice_client is not None:
                    if self.parent.dictionary[ctx.guild.id].voice_client.is_playing():
                        self.parent.dictionary[ctx.guild.id].voice_client.stop()
            if not self.parent.dictionary[ctx.guild.id].voice_client.is_playing():
                await self.pre_player(ctx)
            await self.preload_song(ctx)
        except Exception as e:
            self.parent.log.error(print(traceback.format_exc()))
            self.parent.log.error(logging_manager.debug_info(str(e)))

    async def join_check(self, ctx, url):
        if url is None:
            await self.parent.send_error_message(
                ctx, "You need to enter something to play."
            )
            return False
        if self.parent.dictionary[ctx.guild.id].voice_channel is None:
            if ctx.author.voice is not None:
                self.parent.dictionary[
                    ctx.guild.id
                ].voice_channel = ctx.author.voice.channel
            else:
                await self.parent.send_error_message(
                    ctx, "You need to be in a channel."
                )
                return False
        if not await self.parent.control_check.same_channel_check(ctx):
            return False
        return True

    async def join_channel(self, ctx):
        if self.parent.dictionary[ctx.guild.id].voice_client is None:
            try:
                if (
                    ctx.author.voice.channel.user_limit
                    <= len(ctx.author.voice.channel.members)
                    and ctx.author.voice.channel.user_limit != 0
                ):
                    if ctx.guild.me.guild_permissions.administrator is True:
                        self.parent.dictionary[
                            ctx.guild.id
                        ].voice_client = await ctx.author.voice.channel.connect(
                            timeout=60, reconnect=True
                        )
                    else:
                        await self.parent.send_embed_message(
                            ctx, "Error while joining your channel. :frowning: (1)"
                        )
                        return False
                else:
                    self.parent.dictionary[
                        ctx.guild.id
                    ].voice_client = await ctx.author.voice.channel.connect(
                        timeout=10, reconnect=True
                    )
            except (
                TimeoutError,
                discord.HTTPException,
                discord.ClientException,
                discord.DiscordException,
                Exception,
            ) as e:
                self.parent.log.warning(
                    logging_manager.debug_info("channel_join " + str(e))
                )
                self.parent.dictionary[ctx.guild.id].voice_channel = None
                await self.parent.send_embed_message(
                    ctx, "Error while joining your channel. :frowning: (2)"
                )
                return False
        return True

    # @commands.cooldown(1, 0.5, commands.BucketType.guild)
    @commands.command(aliases=["p"])
    async def play(self, ctx, *, url: str = None):
        if not await self.play_check(ctx, url):
            return
        await self.add_to_queue(url, ctx)

    @commands.command(aliases=["pn"])
    async def playnext(self, ctx, *, url: str = None):
        if not await self.play_check(ctx, url):
            return
        await self.add_to_queue(url, ctx, first_index_push=True)

    @commands.command(aliases=["ps"])
    async def playskip(self, ctx, *, url: str = None):
        if not await self.play_check(ctx, url):
            return
        await self.add_to_queue(url, ctx, playskip=True)

    async def play_check(self, ctx, url):
        if not await self.join_check(ctx, url):
            return False
        if not await self.join_channel(ctx=ctx):
            return False

        yt = YouTubeType(url)
        sp = SpotifyType(url)

        if yt.valid or sp.valid or url.lower() == "charts":
            return True
        if re.match(VariableStore.url_pattern, url) is not None:
            await self.parent.send_embed_message(
                ctx, "This is not a valid/supported url."
            )
            return False
        return True

    def song_conclusion(self, ctx, error=None):
        if len(self.parent.dictionary[ctx.guild.id].song_queue.queue) == 0:
            self.parent.dictionary[ctx.guild.id].now_playing = None
        if error is not None:
            self.parent.log.error(str(error))
            function = asyncio.run_coroutine_threadsafe(
                self.parent.send_error_message(ctx, str(error)), self.bot.loop
            )
            try:
                function.result()
            except Exception as e:
                self.parent.log.error(e)
        function = asyncio.run_coroutine_threadsafe(
            self.parent.clear_presence(ctx), self.bot.loop
        )
        try:
            function.result()
        except Exception as e:
            self.parent.log.error(traceback.format_exc())
            self.parent.log.error(logging_manager.debug_info(str(e)))
        function = asyncio.run_coroutine_threadsafe(
            self.empty_channel(ctx), self.bot.loop
        )
        try:
            function.result()
        except Exception as e:
            self.parent.log.error(traceback.print_exc())
            self.parent.log.error(logging_manager.debug_info(str(e)))
        function = asyncio.run_coroutine_threadsafe(self.pre_player(ctx), self.bot.loop)
        try:
            function.result()
        except Exception as e:
            self.parent.log.error(logging_manager.debug_info(str(e)))

    async def player(self, ctx, small_dict):
        if isinstance(small_dict, Error):
            error_message = small_dict.reason
            await self.parent.send_error_message(ctx, error_message)
            if error_message in (Errors.no_results_found, Errors.default):
                await self.parent.dictionary[ctx.guild.id].now_playing_message.delete()
                return

            small_dict = await self.parent.youtube.youtube_url(small_dict.link)

            if isinstance(small_dict, Error):
                self.parent.log.error(small_dict.reason)
                await self.parent.send_error_message(ctx, small_dict.reason)
                return

        try:
            self.parent.dictionary[ctx.guild.id].now_playing = small_dict
            if self.parent.dictionary[ctx.guild.id].voice_client is None:
                return
            volume = await self.parent.mongo.get_volume(ctx.guild.id)
            source = PCMVolumeTransformerB(
                FFmpegPCMAudioB(
                    small_dict.stream,
                    executable="ffmpeg",
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                ),
                volume=volume,
            )
            try:
                self.parent.dictionary[ctx.guild.id].voice_client.play(
                    source, after=lambda error: self.song_conclusion(ctx, error=error)
                )
            except discord.ClientException:
                if ctx.guild.voice_client is None:
                    if self.parent.dictionary[ctx.guild.id].voice_channel is not None:
                        self.parent.dictionary[
                            ctx.guild.id
                        ].voice_client = await self.parent.dictionary[
                            ctx.guild.id
                        ].voice_channel.connect(
                            timeout=10, reconnect=True
                        )
                        self.parent.dictionary[ctx.guild.id].voice_client.play(
                            source,
                            after=lambda error: self.song_conclusion(ctx, error=error),
                        )
            full, empty = await self.parent.mongo.get_chars(ctx.guild.id)
            self.parent.dictionary[
                ctx.guild.id
            ].now_playing_message = NowPlayingMessage(
                ctx=ctx,
                message=self.parent.dictionary[
                    ctx.guild.id
                ].now_playing_message.message,
                song=self.parent.dictionary[ctx.guild.id].now_playing,
                full=full,
                empty=empty,
                discord_music=self.parent,
                voice_client=self.parent.dictionary[ctx.guild.id].voice_client,
            )
            await self.parent.dictionary[ctx.guild.id].now_playing_message.send()
            if environ.get("USE_EMBEDS", "True") == "True":
                asyncio.ensure_future(
                    self.parent.dictionary[ctx.guild.id].now_playing_message.update()
                )

        except (Exception, discord.ClientException) as e:
            self.parent.log.debug(logging_manager.debug_info(traceback.format_exc(e)))

    async def preload_song(self, ctx):
        """
        Preload of the next song.
        :param ctx:
        :return:
        """
        try:
            if self.parent.dictionary[ctx.guild.id].song_queue.qsize() > 0:
                i = 0
                for item in self.parent.dictionary[ctx.guild.id].song_queue.queue:
                    item: Song
                    if item.stream is None:
                        backup_title: str = str(item.title)
                        if item.link is not None:
                            youtube_dict = await self.parent.youtube.youtube_url(
                                item.link
                            )
                            youtube_dict.user = item.user
                        else:
                            if item.title is not None:
                                youtube_dict = await self.parent.youtube.youtube_term(
                                    item.title
                                )
                            else:
                                youtube_dict = await self.parent.youtube.youtube_term(
                                    item.term
                                )
                            youtube_dict.user = item.user
                        j: int = 0

                        for _song in self.parent.dictionary[
                            ctx.guild.id
                        ].song_queue.queue:
                            _song: Song
                            if _song.title == backup_title:
                                self.parent.dictionary[ctx.guild.id].song_queue.queue[
                                    j
                                ] = youtube_dict
                                break
                            j -= -1
                        break
                    i += 1
        except IndexError:
            pass

    async def empty_channel(self, ctx):
        """
        Leaves the channel if the bot is alone
        :param ctx:
        :return:
        """
        if len(self.parent.dictionary[ctx.guild.id].voice_channel.members) == 1:
            if (
                self.parent.dictionary[ctx.guild.id].voice_channel.members[0]
                == ctx.guild.me
            ):
                self.parent.dictionary[ctx.guild.id].song_queue = Queue()
                await self.parent.dictionary[ctx.guild.id].voice_client.disconnect()
                await self.parent.send_embed_message(
                    ctx=ctx, message="I've left the channel, because it was empty."
                )
