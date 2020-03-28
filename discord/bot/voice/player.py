import asyncio
import random
import re
import traceback
from typing import Dict

import bot.node_controller.NodeVoiceClient
import discord
import logging_manager
from bot.node_controller.controller import NoNodeReadyException
from bot.now_playing_message import NowPlayingMessage
from bot.type.errors import Errors
from bot.type.exceptions import (
    BasicError,
    NoResultsFound,
    PlaylistExtractionException,
    SongExtractionException,
)
from bot.type.guild import Guild
from bot.type.song import Song
from bot.type.soundcloud_type import SoundCloudType
from bot.type.spotify_song import SpotifySong
from bot.type.spotify_type import SpotifyType
from bot.type.url import Url
from bot.type.variable_store import VariableStore
from bot.type.youtube_type import YouTubeType
from bot.voice.checks import Checks
from discord.ext import commands
from discord.ext.commands import Cog


class Player(Cog):
    def __init__(self, _bot, parent):
        self.bot = _bot
        self.parent = parent
        self.guilds: Dict[int, Guild] = self.parent.guilds

    async def _search_song(self, ctx: commands.Context, song: Song) -> Song:
        search_service: str = self.guilds[ctx.guild.id].service
        self.parent.log.info(f'Using Search Service "{search_service}"')
        if search_service in ("basic", "music"):
            return await self.parent.youtube.youtube_term(
                song=song, service=search_service
            )
        elif search_service == "soundcloud":
            return await self.parent.soundcloud.soundcloud_search(song=song)
        else:
            raise NotImplementedError()

    async def pre_player(self, ctx: commands.Context, bypass=None):
        guild_id = ctx.guild.id
        if self.guilds[guild_id].song_queue.qsize() > 0 or bypass is not None:
            if bypass is None:
                small_dict = await self.guilds[ctx.guild.id].song_queue.get()
            else:
                small_dict = bypass
            if small_dict.stream is None:
                try:
                    if small_dict.link is not None:
                        # url
                        _type = Url.determine_source(small_dict.link)
                        if _type == Url.youtube:
                            youtube_dict = Song.copy_song(
                                await self.parent.youtube.youtube_url(
                                    small_dict.link, ctx.guild.id
                                ),
                                small_dict,
                            )
                        elif _type == Url.soundcloud:
                            youtube_dict = Song.copy_song(
                                await self.parent.soundcloud.soundcloud_track(
                                    small_dict.link
                                ),
                                small_dict,
                            )
                        else:
                            self.parent.log.warning(
                                "Incompatible Song Type: " + _type
                            )
                            return
                    else:
                        if small_dict.title is None:
                            self.parent.log.warning(small_dict)
                        # term
                        youtube_dict = Song.copy_song(
                            await self._search_song(ctx, small_dict), small_dict
                        )
                except NoResultsFound:
                    await self.parent.send_error_message(
                        ctx, Errors.no_results_found
                    )
                    self.guilds[guild_id].queue_lock = False
                    await self.pre_player(ctx)
                    return
                except SongExtractionException:
                    await self.parent.send_error_message(
                        ctx, Errors.youtube_video_not_available
                    )
                    self.guilds[guild_id].queue_lock = False
                    await self.pre_player(ctx)
                    return
                except BasicError as be:
                    if str(be) != Errors.error_please_retry:
                        await self.parent.send_error_message(ctx, str(be))
                        self.guilds[guild_id].queue_lock = False
                        await self.pre_player(ctx)
                        return
                    return await self.pre_player(ctx, bypass=small_dict)
                youtube_dict.user = small_dict.user
                youtube_dict.image_url = small_dict.image_url
                await self.player(ctx, youtube_dict)

                # add stats to website
                if hasattr(youtube_dict, "title"):
                    asyncio.ensure_future(
                        self.parent.mongo.append_most_played(youtube_dict.title)
                    )
                if hasattr(youtube_dict, "loadtime"):
                    asyncio.ensure_future(
                        self.parent.mongo.append_response_time(
                            youtube_dict.loadtime
                        )
                    )
            else:
                await self.player(ctx, small_dict)
                if hasattr(small_dict, "title"):
                    asyncio.ensure_future(
                        self.parent.mongo.append_most_played(small_dict.title)
                    )
                if hasattr(small_dict, "loadtime"):
                    asyncio.ensure_future(
                        self.parent.mongo.append_response_time(
                            small_dict.loadtime
                        )
                    )

            asyncio.ensure_future(self.preload_song(ctx=ctx))

    async def extract_infos(self, url, ctx):
        url_type = Url.determine_source(url=url)
        if url_type == Url.youtube:
            return await self.extract_first_infos_youtube(url=url, ctx=ctx)
        if url_type == Url.spotify:
            return await self.extract_first_infos_spotify(url=url, ctx=ctx)
        if url_type == Url.soundcloud:
            return await self.extract_first_infos_soundcloud(url=url, ctx=ctx)
        return await self.extract_first_infos_other(url=url, ctx=ctx)

    async def extract_first_infos_youtube(self, url, ctx):
        youtube_type = Url.determine_youtube_type(url=url)
        if youtube_type == Url.youtube_url:
            __song = Song()
            __song.user = ctx.message.author
            __song.link = url
            return [__song]
        if youtube_type == Url.youtube_playlist:
            __songs = []
            __song_list = await self.parent.youtube.youtube_playlist(url)
            if len(__song_list) == 0:
                await self.parent.send_error_message(ctx, Errors.playlist_pull)
                return []
            for track in __song_list:
                track.user = ctx.message.author
                __songs.append(track)
            return __songs

    async def extract_first_infos_soundcloud(self, url, ctx):
        soundcloud_type = Url.determine_soundcloud_type(url)
        if soundcloud_type == Url.soundcloud_track:
            try:
                song: Song = await self.parent.soundcloud.soundcloud_track(url)
                if song.title is None:
                    await self.parent.send_error_message(
                        ctx=ctx, message=Errors.default
                    )
            except BasicError as e:
                await self.parent.send_error_message(ctx=ctx, message=str(e))
                return []
            song.user = ctx.message.author
            return [song]
        if soundcloud_type == Url.soundcloud_set:
            songs: list = await self.parent.soundcloud.soundcloud_playlist(
                url=url
            )
            for song in songs:
                song.user = ctx.message.author
            return songs

    async def extract_first_infos_spotify(self, url, ctx):
        spotify_type = Url.determine_spotify_type(url=url)
        __songs = []
        __song = Song()
        __song.user = ctx.message.author
        if spotify_type == Url.spotify_playlist:
            __song_list = await self.parent.spotify.spotify_playlist(url)
            if len(__song_list) == 0:
                await self.parent.send_error_message(
                    ctx=ctx, message=Errors.playlist_pull
                )
                return []
            for track in __song_list:
                track: SpotifySong
                __song = Song(song=__song)
                __song.title = track.title
                __song.image_url = track.image_url
                __song.artist = track.artist
                __song.song_name = track.song_name
                __songs.append(__song)
            return __songs
        if spotify_type == Url.spotify_track:
            track = await self.parent.spotify.spotify_track(url)
            if track is not None:
                __song.title = track.title
                __song.image_url = track.image_url
                __song.artist = track.artist
                __song.song_name = track.song_name
                return [__song]
            return []
        if spotify_type == Url.spotify_artist:
            song_list = await self.parent.spotify.spotify_artist(url)
            for track in song_list:
                __song = Song(song=__song)
                __song.title = track
                __songs.append(__song)
            return __songs
        if spotify_type == Url.spotify_album:
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
            song_list = await self.extract_first_infos_spotify(
                "https://open.spotify.com/playlist/37i9dQZEVXbMDoHDwVN2tF?si=vgYiEOfYTL-ejBdn0A_E2g",
                ctx,
            )
            for track in song_list:
                track.user = ctx.message.author
                __songs.append(track)
            return __songs
        __song = Song()
        __song.title = url
        __song.user = ctx.message.author
        return [__song]

    async def add_to_queue(
        self, url, ctx, first_index_push=False, playskip=False, shuffle=False
    ):
        try:
            change = (
                not self.guilds[ctx.guild.id].voice_client.node
                in self.parent.node_controller.nodes.values()
            )
        except AttributeError:
            change = False

        try:
            songs: list = await self.extract_infos(url=url, ctx=ctx)
        except NoResultsFound:
            await self.parent.send_error_message(ctx, Errors.no_results_found)
            return
        except PlaylistExtractionException:
            await self.parent.send_error_message(ctx, Errors.playlist_pull)
            return
        except SongExtractionException:
            await self.parent.send_error_message(
                ctx, Errors.youtube_video_not_available
            )
            return

        if playskip:
            self.guilds[ctx.guild.id].song_queue.clear()

        for song in songs:
            song: Song
            song.guild_id = ctx.guild.id
        if len(songs) > 1:
            if shuffle:
                random.shuffle(songs)
            self.guilds[ctx.guild.id].song_queue.queue.extend(songs)
            await self.parent.send_embed_message(
                ctx=ctx,
                message=":asterisk: Added "
                + str(len(songs))
                + " Tracks to Queue. :asterisk:",
            )
        elif len(songs) == 1:
            if first_index_push:
                self.guilds[ctx.guild.id].song_queue.queue.extendleft(songs)
            else:
                self.guilds[ctx.guild.id].song_queue.queue.extend(songs)
            title = ""
            if songs[0].title is not None:
                title = songs[0].title
            else:
                try:
                    title = songs[0].link
                except AttributeError:
                    pass
            if (
                self.guilds[ctx.guild.id].now_playing
                or self.guilds[ctx.guild.id].queue_lock
            ):
                if not playskip and not change:
                    await self.parent.send_embed_message(
                        ctx, ":asterisk: Added **" + title + "** to Queue."
                    )

        # noinspection PyBroadException
        try:
            if change:
                if self.guilds[ctx.guild.id].announce:
                    await ctx.trigger_typing()
                return await self.pre_player(ctx)
            if playskip:
                if self.guilds[ctx.guild.id].voice_client is not None:
                    if self.guilds[ctx.guild.id].voice_client.is_playing():
                        await self.guilds[ctx.guild.id].voice_client.stop()
            if not self.guilds[ctx.guild.id].now_playing:
                if not self.guilds[ctx.guild.id].queue_lock:
                    # locks the queue for direct play
                    self.guilds[ctx.guild.id].queue_lock = True
                    if self.guilds[ctx.guild.id].announce:
                        await ctx.trigger_typing()
                    await self.pre_player(ctx)
        except Exception:
            self.parent.log.error(
                logging_manager.debug_info(traceback.format_exc())
            )

    async def join_check(self, ctx: commands.Context):
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

    async def join_channel(self, ctx):
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
                    ].voice_client = await bot.node_controller.NodeVoiceClient.NodeVoiceChannel.from_channel(
                        ctx.author.voice.channel, self.parent.node_controller
                    ).connect()
                    self.guilds[
                        ctx.guild.id
                    ].now_playing_message = NowPlayingMessage(ctx, self.parent)
            except (
                TimeoutError,
                discord.HTTPException,
                discord.ClientException,
            ) as e:
                self.parent.log.warning(
                    logging_manager.debug_info("channel_join " + str(e))
                )
                self.guilds[ctx.guild.id].voice_channel = None
                await self.parent.send_embed_message(
                    ctx, "Error while joining your channel. :frowning: (2)"
                )
                return False
            except NoNodeReadyException as nn:
                await self.parent.send_error_message(ctx, str(nn))
                return False
        return True

    # @commands.cooldown(1, 0.5, commands.BucketType.guild)
    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["p"])
    async def play(self, ctx, *, url):
        """
        Plays a song.
        :param ctx:
        :param url:
        :return:
        """
        if not await self.play_check(ctx, url):
            return
        await self.add_to_queue(url, ctx)

    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["pn"])
    async def playnext(self, ctx, *, url: str):
        """
        Adds a song to the first position in the queue.
        """
        if not await self.play_check(ctx, url):
            return
        await self.add_to_queue(url, ctx, first_index_push=True)

    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["ps"])
    async def playskip(self, ctx, *, url: str):
        """
        Queues a song and instantly skips to it.
        :param ctx:
        :param url:
        :return:
        """
        if not await self.play_check(ctx, url):
            return
        await self.add_to_queue(url, ctx, playskip=True)

    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["sp"])
    async def shuffleplay(self, ctx, *, url: str):
        """
        Queues multiple songs in random order.
        :param ctx:
        :param url:
        :return:
        """
        if not await self.play_check(ctx, url):
            return
        await self.add_to_queue(url, ctx, shuffle=True)

    @play.error
    @playnext.error
    @playskip.error
    @shuffleplay.error
    async def _play_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.MissingRequiredArgument):
            return await self.parent.send_error_message(
                ctx, "You need to enter something to play."
            )

    @commands.check(Checks.user_connection_check)
    @commands.command(aliases=["join"])
    async def connect(self, ctx):
        """
        Connects the bot to your channel.
        :param ctx:
        :return:
        """
        was_connected = self.guilds[ctx.guild.id].voice_client is not None
        if not await self.join_channel(ctx=ctx):
            return
        if was_connected:
            return await self.parent.send_error_message(
                ctx, "Already Connected."
            )
        return await self.parent.send_embed_message(ctx, "Connected.")

    async def play_check(self, ctx, url):
        if not await self.join_check(ctx):
            return False
        if not await self.join_channel(ctx=ctx):
            return False

        yt = YouTubeType(url)
        sp = SpotifyType(url)
        sc = SoundCloudType(url)

        if yt.valid or sp.valid or sc.valid or url.lower() == "charts":
            return True
        if re.match(VariableStore.url_pattern, url) is not None:
            await self.parent.send_embed_message(
                ctx, "This is not a valid/supported url."
            )
            return False
        return True

    async def song_conclusion(self, ctx: commands.Context):
        """
        Things to do after a song is finished.
        :param ctx: Context
        :return: nothing
        """
        guild_id = ctx.guild.id
        if len(self.guilds[guild_id].song_queue.queue) == 0:
            self.guilds[guild_id].now_playing = None
        # catch all one after another to make most of them succeed

        async def _player_wrapper(_ctx: commands.Context):
            if self.guilds[guild_id].voice_client:
                if self.guilds[guild_id].voice_client.is_connected():
                    return await self.pre_player(_ctx)

        tasks = []
        if self.guilds[guild_id].announce:
            if self.guilds[guild_id].now_playing_message:
                tasks.append(
                    self.guilds[guild_id].now_playing_message.after_song()
                )
        tasks.append(_player_wrapper(ctx))
        for task in tasks:
            # noinspection PyBroadException
            try:
                await task
            except Exception as e:
                self.parent.log.error(traceback.format_exc(e))

    async def player(self, ctx, small_dict):
        try:
            self.guilds[ctx.guild.id].now_playing = small_dict
            self.guilds[ctx.guild.id].queue_lock = False
            if self.guilds[ctx.guild.id].voice_client is None:
                return
            try:
                small_dict.guild_id = ctx.guild.id
                await self.guilds[ctx.guild.id].voice_client.play(small_dict)
                self.guilds[ctx.guild.id].voice_client.set_after(
                    self.song_conclusion, ctx
                )
            except discord.ClientException:
                if ctx.guild.voice_client is None:
                    if self.guilds[ctx.guild.id].voice_channel is not None:
                        self.guilds[
                            ctx.guild.id
                        ].voice_client = await self.guilds[
                            ctx.guild.id
                        ].voice_channel.connect(
                            timeout=10, reconnect=True
                        )
                        small_dict.guild_id = ctx.guild.id
                        await self.guilds[ctx.guild.id].voice_client.play(
                            small_dict,
                            # after=lambda error: self.song_conclusion(
                            #    ctx, error=error
                            # ),
                        )
                        self.guilds[ctx.guild.id].voice_client.set_after(
                            self.song_conclusion, ctx
                        )
            if self.guilds[ctx.guild.id].announce:
                await self.guilds[ctx.guild.id].now_playing_message.new_song()
        except (Exception, discord.ClientException) as e:
            self.parent.log.debug(
                logging_manager.debug_info(traceback.format_exc(e))
            )

    async def preload_song(self, ctx):
        """
        Preload of the next song.
        :param ctx:
        :return:
        """
        try:
            if self.guilds[ctx.guild.id].song_queue.qsize() > 0:
                i = 0
                for item in self.guilds[ctx.guild.id].song_queue.queue:
                    item: Song
                    if item.stream is None:
                        backup_title: str = str(item.title)
                        if item.link is not None:
                            try:
                                type_of_source = Url.determine_source(item.link)
                                if type_of_source == Url.youtube_url:
                                    youtube_dict = await self.parent.youtube.youtube_url(
                                        item.link, ctx.guild.id
                                    )
                                elif type_of_source == Url.soundcloud_track:
                                    youtube_dict = await self.parent.soundcloud.soundcloud_track(
                                        item.link
                                    )
                                else:
                                    continue
                            except BasicError:
                                self.parent.log(
                                    logging_manager.debug_info(
                                        traceback.format_exc()
                                    )
                                )
                                continue
                            youtube_dict.user = item.user
                        else:
                            if item.title is not None:
                                try:
                                    youtube_dict = await self._search_song(
                                        ctx, item
                                    )
                                except BasicError:
                                    continue
                            youtube_dict.user = item.user
                        j: int = 0

                        for _song in self.guilds[ctx.guild.id].song_queue.queue:
                            _song: Song
                            if _song.title == backup_title:
                                self.guilds[ctx.guild.id].song_queue.queue[
                                    j
                                ] = Song.copy_song(
                                    youtube_dict,
                                    self.guilds[ctx.guild.id].song_queue.queue[
                                        j
                                    ],
                                )
                                break
                            j -= -1
                        break
                    i += 1
        except IndexError:
            pass
        except AttributeError:
            traceback.print_exc()
