"""
Player
"""
import asyncio
import random
import re
import traceback
from typing import TYPE_CHECKING, Dict, List, Optional, Type

import discord
from discord.ext import commands
from discord.ext.commands import Cog

import logging_manager
from bot.node_controller.controller import NoNodeReadyException
from bot.node_controller.node_voice_client import NodeVoiceChannel
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
from bot.type.spotify_type import SpotifyType
from bot.type.url import Url
from bot.type.variable_store import VariableStore
from bot.type.youtube_type import YouTubeType
from bot.voice.checks import Checks

if TYPE_CHECKING:
    # pylint: disable=ungrouped-imports
    from bot.discord_music import DiscordBot


class Player(Cog):
    """
    Player
    """

    def __init__(self, _bot: commands.Bot, parent: "DiscordBot") -> None:
        self.bot: commands.Bot = _bot
        self.parent: "DiscordBot" = parent
        self.guilds: Dict[int, Guild] = self.parent.guilds

    async def _search_song(self, ctx: commands.Context, song: Song) -> Song:
        search_service: str = self.guilds[ctx.guild.id].service
        self.parent.log.info(f'Using Search Service "{search_service}"')
        if search_service in ("basic", "music"):
            return await self.parent.youtube.youtube_term(
                song=song, service=search_service
            )
        if search_service == "soundcloud":
            return await self.parent.soundcloud.soundcloud_search(song=song)
        raise NotImplementedError()

    async def pre_player(self, ctx: commands.Context, bypass=None) -> None:
        """
        Routine called before a song gets played.
        @param ctx:
        @param bypass:
        @return:
        """
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
                                f"Incompatible Song Type: {_type}"
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
                except BasicError as basic_error:
                    if str(basic_error) != Errors.error_please_retry:
                        await self.parent.send_error_message(
                            ctx, str(basic_error)
                        )
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

    async def extract_infos(
        self, url: str, ctx: commands.Context
    ) -> List[Song]:
        """
        Method to extract first information from multiple sources
        @param url:
        @param ctx:
        @return:
        """
        url_type = Url.determine_source(url=url)
        if url_type == Url.youtube:
            return await self._extract_first_infos_youtube(url=url, ctx=ctx)
        if url_type == Url.spotify:
            return await self._extract_first_infos_spotify(url=url, ctx=ctx)
        if url_type == Url.soundcloud:
            return await self._extract_first_infos_soundcloud(url=url, ctx=ctx)
        return await self._extract_first_infos_other(url=url, ctx=ctx)

    async def _extract_first_infos_youtube(
        self, url: str, ctx: commands.Context
    ) -> List[Song]:
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

    async def _extract_first_infos_soundcloud(
        self, url: str, ctx: commands.Context
    ) -> List[Song]:
        soundcloud_type = Url.determine_soundcloud_type(url)
        if soundcloud_type == Url.soundcloud_track:
            try:
                song: Song = await self.parent.soundcloud.soundcloud_track(url)
                if song.title is None:
                    await self.parent.send_error_message(
                        ctx=ctx, message=Errors.default
                    )
            except BasicError as basic_error:
                await self.parent.send_error_message(
                    ctx=ctx, message=str(basic_error)
                )
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

    async def _extract_first_infos_spotify(
        self, url: str, ctx: commands.Context
    ) -> List[Song]:
        spotify_type = Url.determine_spotify_type(url=url)
        __songs = []
        __song = Song()
        __song.user = ctx.message.author
        if spotify_type == Url.spotify_playlist:
            song_list = await self.parent.spotify.spotify_playlist(url)
            return song_list
        if spotify_type == Url.spotify_track:
            track = await self.parent.spotify.spotify_track(url)
            if track:
                return [track]
            return []
        if spotify_type == Url.spotify_artist:
            song_list = await self.parent.spotify.spotify_artist(url)
            return song_list
        if spotify_type == Url.spotify_album:
            song_list = await self.parent.spotify.spotify_album(url)
            return song_list

    async def _extract_first_infos_other(
        self, url: str, ctx: commands.Context
    ) -> List[Song]:
        if url == "charts":
            __songs = []
            __song = Song()
            __song.user = ctx.message.author
            song_list = await self._extract_first_infos_spotify(
                "https://open.spotify.com/playlist/37i9dQZEVXbMD"
                "oHDwVN2tF?si=vgYiEOfYTL-ejBdn0A_E2g",
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
        self,
        url: str,
        ctx: commands.Context,
        first_index_push: bool = False,
        play_skip: bool = False,
        shuffle: bool = False,
    ):
        """
        Add a new song to the queue.
        @param url: url / term of song
        @param ctx: dpy context
        @param first_index_push: if true the new song gets appended on the left
        of the queue
        @param play_skip: if true the song will be instantly skipped to
        @param shuffle: if true and mulitple songs were extracted,
        the songs will be placed in the queue in random order
        @return:
        """
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

        if play_skip:
            self.guilds[ctx.guild.id].song_queue.clear()

        for song in songs:
            song: Song
            song.guild_id = ctx.guild.id
            song.user = ctx.message.author
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
                if not play_skip and not change:
                    await self.parent.send_embed_message(
                        ctx, ":asterisk: Added **" + title + "** to Queue."
                    )

        # noinspection PyBroadException
        try:
            if change:
                if self.guilds[ctx.guild.id].announce:
                    await ctx.trigger_typing()
                return await self.pre_player(ctx)
            if play_skip:
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
            except (
                TimeoutError,
                discord.HTTPException,
                discord.ClientException,
            ) as discord_error:
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

    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, url: str) -> None:
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
    @commands.command(aliases=["pn", "playnext"])
    async def play_next(self, ctx: commands.Context, *, url: str) -> None:
        """
        Adds a song to the first position of the queue
        @param ctx:
        @param url:
        @return:
        """
        if not await self.play_check(ctx, url):
            return
        await self.add_to_queue(url, ctx, first_index_push=True)

    @commands.check(Checks.same_channel_check)
    @commands.command(aliases=["ps", "playskip"])
    async def play_skip(self, ctx: commands.Context, *, url: str) -> None:
        """
        Queues a song and instantly skips to it.
        :param ctx:
        :param url:
        :return:
        """
        if not await self.play_check(ctx, url):
            return
        await self.add_to_queue(url, ctx, play_skip=True)

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
    @play_next.error
    @play_skip.error
    @shuffleplay.error
    async def _play_error(
        self, ctx: commands.Context, error: Type[discord.DiscordException]
    ) -> discord.Message:
        if isinstance(error, discord.ext.commands.MissingRequiredArgument):
            return await self.parent.send_error_message(
                ctx, "You need to enter something to play."
            )

    @commands.check(Checks.user_connection_check)
    @commands.command(aliases=["join"])
    async def connect(self, ctx: commands.Context) -> Optional[discord.Message]:
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

        youtube_type = YouTubeType(url)
        spotify_type = SpotifyType(url)
        soundcloud_type = SoundCloudType(url)

        if (
            youtube_type.valid
            or spotify_type.valid
            or soundcloud_type.valid
            or url.lower() == "charts"
        ):
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
        if (
            len(self.guilds[guild_id].song_queue.queue) == 0
            or not self.guilds[guild_id].voice_client
        ):
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
                    self.guilds[guild_id].now_playing_message.after_song(
                        ctx=ctx
                    )
                )
        tasks.append(_player_wrapper(ctx))
        for task in tasks:
            # noinspection PyBroadException
            try:
                await task
            except Exception as thrown_exception:
                self.parent.log.error(traceback.format_exc(thrown_exception))

    async def player(self, ctx: commands.Context, small_dict: Song) -> None:
        """
        Plays a Song.
        @param ctx:
        @param small_dict:
        @return:
        """
        try:
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
                        )
                        self.guilds[ctx.guild.id].voice_client.set_after(
                            self.song_conclusion, ctx
                        )
            self.guilds[ctx.guild.id].now_playing = small_dict
            if self.guilds[ctx.guild.id].announce:
                if not self.guilds[ctx.guild.id].now_playing_message:
                    self.guilds[
                        ctx.guild.id
                    ].now_playing_message = NowPlayingMessage(self.parent)
                await self.guilds[ctx.guild.id].now_playing_message.new_song(
                    ctx=ctx
                )
        except (Exception, discord.ClientException) as discord_exception:
            self.parent.log.debug(
                logging_manager.debug_info(
                    traceback.format_exc(discord_exception)
                )
            )

    async def preload_song(self, ctx: commands.Context) -> None:
        """
        Preload of the next song.
        :param ctx:
        :return:
        """
        try:
            if self.guilds[ctx.guild.id].song_queue.qsize() == 0:
                return
            i = 0
            for item in self.guilds[ctx.guild.id].song_queue.queue:
                item: Song
                if item.stream:
                    continue
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
                            logging_manager.debug_info(traceback.format_exc())
                        )
                        continue
                    youtube_dict.user = item.user
                else:
                    if item.title:
                        continue
                    try:
                        youtube_dict = await self._search_song(ctx, item)
                    except BasicError:
                        continue
                    youtube_dict.user = item.user
                j: int = 0

                for _song in self.guilds[ctx.guild.id].song_queue.queue:
                    _song: Song
                    if _song.title != backup_title:
                        j += 1
                        continue
                    self.guilds[ctx.guild.id].song_queue.queue[
                        j
                    ] = Song.copy_song(
                        youtube_dict,
                        self.guilds[ctx.guild.id].song_queue.queue[j],
                    )
                    break
                break
            i += 1
        except IndexError:
            pass
        except AttributeError:
            traceback.print_exc()
