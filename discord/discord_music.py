import traceback
import time
import string
from typing import Dict

import logging_manager
import collections
import re
import discord
import random
import asyncio
import async_timeout
import dbl

from os import environ
from discord.ext import commands

from extractors import spotify
from extractors import mongo
from extractors import lastfm

from variable_store import VariableStore
from variable_store import Errors
from variable_store import Queue

from url_parser import YouTubeType
from url_parser import SpotifyType

from song_store import Song
from song_store import Guild
from song_store import Error

from now_playing_message import NowPlayingMessage

from FFmpegPCMAudio import FFmpegPCMAudioB
from FFmpegPCMAudio import PCMVolumeTransformerB


class DiscordBot(commands.Cog):
    def __init__(self, bot):
        self.dictionary: Dict[Guild] = {}
        self.bot = bot
        self.log = logging_manager.LoggingManager()
        self.spotify = spotify.Spotify()
        self.mongo = mongo.Mongo()
        if environ.get("OLD_BACKEND", False) is True:
            from extractors import youtube_old

            self.youtube = youtube_old.Youtube(mongo_client=self.mongo)
        else:
            from extractors import youtube

            self.youtube = youtube.Youtube(mongo_client=self.mongo)
        self.lastfm = lastfm.LastFM()
        bot.remove_command("help")
        self.log.debug("[Startup]: Initializing Music Module . . .")

        def generate_key(length):
            letters = string.ascii_letters
            response = ""
            for a in range(0, length):
                response += random.choice(letters)
            return response

        restart_key = generate_key(64)
        asyncio.run_coroutine_threadsafe(
            self.mongo.set_restart_key(restart_key), self.bot.loop
        )

        # Fix for OpusNotLoaded Error.
        if not discord.opus.is_loaded():
            discord.opus.load_opus("/usr/lib/libopus.so")

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

                if self.dictionary[guild_id].voice_channel is None:
                    return
                if member is self.bot.user:
                    if self.bot.get_guild(guild_id).voice_client is not None:
                        self.dictionary[guild_id].voice_channel = None
                        self.dictionary[guild_id].voice_client = None
                        return

                if (
                    self.dictionary[guild_id].voice_channel is before.channel
                    and self.dictionary[guild_id].voice_channel is not after.channel
                ):
                    if len(before.channel.members) == 1:
                        asyncio.ensure_future(
                            self.check_my_channel(before.channel, guild_id)
                        )
            except KeyError:
                pass

        @self.bot.event
        async def on_guild_join(guild):
            """
            Triggers if someone joins a guild and adds it to memory
            :param guild: the server joined
            :return:
            """
            self.log.debug("Joined a new Guild! Hello, " + guild.name)
            self.dictionary[guild.id] = Guild()

        for _guild in self.bot.guilds:
            self.dictionary[_guild.id] = Guild()
            if _guild.me.voice is not None:
                if hasattr(_guild.me.voice, "channel"):

                    async def reconnect(_guild):
                        """
                        Reconnects disconnected clients after restart
                        :param _guild: guild
                        :return:
                        """
                        self.log.debug("[Reconnect] Reconnecting " + str(_guild))
                        self.dictionary[
                            _guild.id
                        ].voice_channel = _guild.me.voice.channel
                        t = await _guild.me.voice.channel.connect(
                            timeout=5, reconnect=False
                        )
                        await t.disconnect(force=True)
                        self.dictionary[
                            _guild.id
                        ].voice_client = await _guild.me.voice.channel.connect(
                            timeout=5, reconnect=True
                        )

                    asyncio.run_coroutine_threadsafe(reconnect(_guild), self.bot.loop)

        self.dbl_key = environ.get("DBL_KEY", "")
        if self.dbl_key != "":
            self.dbl_client = dbl.DBLClient(self.bot, self.dbl_key)

            async def update_stats():
                while not self.bot.is_closed():
                    try:
                        await self.dbl_client.post_guild_count()
                        self.log.debug(
                            "[SERVER COUNT] Posted server count ({})".format(
                                self.dbl_client.guild_count()
                            )
                        )
                        await self.bot.change_presence(
                            activity=discord.Activity(
                                type=discord.ActivityType.listening,
                                name=".help on {} servers".format(
                                    self.dbl_client.guild_count()
                                ),
                            )
                        )
                    except Exception as e:
                        self.log.warning(logging_manager.debug_info(e))
                    await asyncio.sleep(1800)

            self.bot.loop.create_task(update_stats())

    @staticmethod
    async def send_embed_message(
        ctx: discord.ext.commands.Context, message: str, delete_after: float = None
    ):
        if environ.get("USE_EMBEDS", "True") == "True":
            embed = discord.Embed(
                title=message, url="https://d.chulte.de", colour=0x00FFCC
            )
            return await ctx.send(embed=embed, delete_after=delete_after)
        return await ctx.send(message, delete_after=delete_after)

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
                    if self.dictionary[guild_id].voice_channel is not channel:
                        return
                    if len(self.dictionary[guild_id].voice_channel.members) > 1:
                        return
                    if time.time() == 0:
                        break
        except asyncio.TimeoutError:
            if self.dictionary[guild_id].voice_client is not None:
                # await self.dictionary[guild_id].voice_client.disconnect()
                self.dictionary[guild_id].song_queue = Queue()
                self.dictionary[guild_id].voice_client.stop()

    async def __same_channel_check(self, ctx: discord.ext.commands.Context):
        """
        checks if the user is in the same channel
        :param ctx: context
        :return:
        """
        if ctx.me.voice is not None:
            if ctx.guild.me.voice.channel != ctx.author.voice.channel:
                await self.send_error_message(
                    ctx, "You need to be in the same channel as the bot."
                )
                return False
        return True

    async def __user_connection_check(self, ctx):
        try:
            if not hasattr(ctx.author.voice, "channel"):
                await self.send_error_message(ctx, "You need to be in a channel.")
                return False
        except AttributeError:
            return False
        return True

    async def __bot_connection_check(self, ctx):
        if ctx.guild.me.voice is None:
            await self.send_error_message(ctx, "The bot isn't connected.")
            return False
        return True

    async def __manipulation_checks(self, ctx):
        return (
            await self.__bot_connection_check(ctx)
            and await self.__user_connection_check(ctx)
            and await self.__same_channel_check(ctx)
        )

    async def clear_presence(self, ctx: discord.ext.commands.Context):
        """
        Stops message updating after a song finished
        :param ctx:
        :return:
        """
        try:
            if self.dictionary[ctx.guild.id].now_playing_message is not None:
                await self.dictionary[ctx.guild.id].now_playing_message.stop()
                try:
                    await ctx.message.delete()
                except discord.NotFound:
                    pass
        except discord.NotFound:
            self.dictionary[ctx.guild.id].now_playing_message = None

    @staticmethod
    async def send_error_message(ctx, message, delete_after=None):
        """
        Sends an error message
        :param delete_after:
        :param ctx: discord.py context
        :param message: the message to send
        :return:
        """
        if environ.get("USE_EMBEDS", "True") == "True":
            embed = discord.Embed(description=message, color=0xFF0000)
            await ctx.send(embed=embed, delete_after=delete_after)
        else:
            await ctx.send(message, delete_after=delete_after)

    async def empty_channel(self, ctx):
        """
        Leaves the channel if the bot is alone
        :param ctx:
        :return:
        """
        if len(self.dictionary[ctx.guild.id].voice_channel.members) == 1:
            if self.dictionary[ctx.guild.id].voice_channel.members[0] == ctx.guild.me:
                self.dictionary[ctx.guild.id].song_queue = Queue()
                await self.dictionary[ctx.guild.id].voice_client.disconnect()
                await self.send_embed_message(
                    ctx=ctx, message="I've left the channel, because it was empty."
                )

    async def preload_song(self, ctx):
        """
        Preload of the next song.
        :param ctx:
        :return:
        """
        try:
            if self.dictionary[ctx.guild.id].song_queue.qsize() > 0:
                i = 0
                for item in self.dictionary[ctx.guild.id].song_queue.queue:
                    item: Song
                    if item.stream is None:
                        backup_title: str = str(item.title)
                        if item.link is not None:
                            youtube_dict = await self.youtube.youtube_url(item.link)
                            youtube_dict.user = item.user
                        else:
                            if item.title is not None:
                                youtube_dict = await self.youtube.youtube_term(
                                    item.title
                                )
                            else:
                                youtube_dict = await self.youtube.youtube_term(
                                    item.term
                                )
                            youtube_dict.user = item.user
                        j: int = 0

                        for _song in self.dictionary[ctx.guild.id].song_queue.queue:
                            _song: Song
                            if _song.title == backup_title:
                                self.dictionary[ctx.guild.id].song_queue.queue[
                                    j
                                ] = youtube_dict
                                break
                            j -= -1
                        break
                    i += 1
        except IndexError:
            pass

    def song_conclusion(self, ctx, error=None):

        if len(self.dictionary[ctx.guild.id].song_queue.queue) == 0:
            self.dictionary[ctx.guild.id].now_playing = None
        if error is not None:
            self.log.error(str(error))
            function = asyncio.run_coroutine_threadsafe(
                self.send_error_message(ctx, str(error)), self.bot.loop
            )
            try:
                function.result()
            except Exception as e:
                self.log.error(e)
        function = asyncio.run_coroutine_threadsafe(
            self.clear_presence(ctx), self.bot.loop
        )
        try:
            function.result()
        except Exception as e:
            self.log.error(traceback.format_exc())
            self.log.error(logging_manager.debug_info(str(e)))
        function = asyncio.run_coroutine_threadsafe(
            self.empty_channel(ctx), self.bot.loop
        )
        try:
            function.result()
        except Exception as e:
            self.log.error(traceback.print_exc())
            self.log.error(logging_manager.debug_info(str(e)))
        function = asyncio.run_coroutine_threadsafe(self.pre_player(ctx), self.bot.loop)
        try:
            function.result()
        except Exception as e:
            self.log.error(logging_manager.debug_info(str(e)))

    async def player(self, ctx, small_dict):
        if isinstance(small_dict, Error):
            error_message = small_dict.reason
            await self.send_error_message(ctx, error_message)
            if (
                error_message == Errors.no_results_found
                or error_message == Errors.default
            ):
                await self.dictionary[ctx.guild.id].now_playing_message.delete()
                return

            small_dict = await self.youtube.youtube_url(small_dict.link)

            if isinstance(small_dict, Error):
                self.log.error(small_dict.reason)
                await self.send_error_message(ctx, small_dict.reason)
                return

        try:
            self.dictionary[ctx.guild.id].now_playing = small_dict
            if self.dictionary[ctx.guild.id].voice_client is None:
                return
            volume = await self.mongo.get_volume(ctx.guild.id)
            source = PCMVolumeTransformerB(
                FFmpegPCMAudioB(
                    small_dict.stream,
                    executable="ffmpeg",
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                ),
                volume=volume,
            )
            try:
                self.dictionary[ctx.guild.id].voice_client.play(
                    source, after=lambda error: self.song_conclusion(ctx, error=error)
                )
            except discord.ClientException:
                if ctx.guild.voice_client is None:
                    if self.dictionary[ctx.guild.id].voice_channel is not None:
                        self.dictionary[
                            ctx.guild.id
                        ].voice_client = await self.dictionary[
                            ctx.guild.id
                        ].voice_channel.connect(
                            timeout=10, reconnect=True
                        )
                        self.dictionary[ctx.guild.id].voice_client.play(
                            source,
                            after=lambda error: self.song_conclusion(ctx, error=error),
                        )
            full, empty = await self.mongo.get_chars(ctx.guild.id)
            self.dictionary[ctx.guild.id].now_playing_message = NowPlayingMessage(
                ctx=ctx,
                message=self.dictionary[ctx.guild.id].now_playing_message.message,
                song=self.dictionary[ctx.guild.id].now_playing,
                full=full,
                empty=empty,
                discord_music=self,
                voice_client=self.dictionary[ctx.guild.id].voice_client,
            )
            await self.dictionary[ctx.guild.id].now_playing_message.send()
            if environ.get("USE_EMBEDS", "True") == "True":
                asyncio.ensure_future(
                    self.dictionary[ctx.guild.id].now_playing_message.update()
                )

        except (Exception, discord.ClientException) as e:
            self.log.debug(logging_manager.debug_info(traceback.format_exc(e)))

    async def preload_album_art(self, ctx):
        try:
            song_title = self.dictionary[ctx.guild.id].now_playing.title
            search_term = self.dictionary[ctx.guild.id].now_playing.term
            if song_title == "_":
                self.dictionary[
                    ctx.guild.id
                ].now_playing.image_url = await self.lastfm.get_album_art(
                    search_term, search_term
                )
            else:
                self.dictionary[
                    ctx.guild.id
                ].now_playing.image_url = await self.lastfm.get_album_art(
                    song_title, search_term
                )
        except (IndexError, TypeError, KeyError, NameError) as e:
            self.log.warning(logging_manager.debug_info(str(e)))

    async def pre_player(self, ctx, bypass=None):
        if self.dictionary[ctx.guild.id].song_queue.qsize() > 0 or bypass is not None:
            if bypass is None:
                small_dict = await self.dictionary[ctx.guild.id].song_queue.get()
            else:
                small_dict = bypass
            self.dictionary[ctx.guild.id].now_playing_message = NowPlayingMessage(
                message=await self.send_embed_message(ctx=ctx, message=" Loading ... "),
                ctx=ctx,
            )
            if small_dict.stream is None:
                if small_dict.link is not None:
                    # url
                    youtube_dict = await self.youtube.youtube_url(small_dict.link)
                else:
                    if small_dict.title is None:
                        self.log.warning(small_dict)
                    # term
                    youtube_dict = await self.youtube.youtube_term(small_dict.title)
                    # youtube_dict = await self.youtube_t.youtube_term(small_dict['title'])
                if isinstance(youtube_dict, Error):
                    if youtube_dict.reason != Errors.error_please_retry:
                        await self.send_error_message(ctx, youtube_dict.reason)
                        await self.dictionary[ctx.guild.id].now_playing_message.delete()
                        await self.pre_player(ctx)
                        return
                    await self.dictionary[ctx.guild.id].now_playing_message.delete()
                    await self.pre_player(ctx, bypass=small_dict)
                    return
                youtube_dict.user = small_dict.user
                youtube_dict.image_url = small_dict.image_url
                await self.player(ctx, youtube_dict)
            else:
                await self.player(ctx, small_dict)

            #  asyncio.ensure_future(self.preload_album_art(ctx=ctx))
            asyncio.ensure_future(self.preload_song(ctx=ctx))

    async def add_to_queue(self, url, ctx, first_index_push=False, playskip=False):
        if playskip:
            self.dictionary[ctx.guild.id].song_queue = Queue()

        small_dict = Song()
        small_dict.user = ctx.message.author

        small_dicts = []

        _multiple = False

        if re.match(VariableStore.youtube_video_pattern, url) is not None:
            if "watch?" in url.lower() or "youtu.be" in url.lower():
                small_dict.link = url
                _multiple = False
            elif "playlist" in url:
                song_list = await self.youtube.youtube_playlist(url)
                if len(song_list) == 0:
                    await self.send_error_message(ctx, Errors.spotify_pull)
                    return
                for track in song_list:
                    track.user = ctx.message.author
                    small_dicts.append(track)
                _multiple = True
        elif (
            re.match(VariableStore.spotify_url_pattern, url) is not None
            or re.match(VariableStore.spotify_uri_pattern, url) is not None
        ):
            if "playlist" in url:
                song_list = await self.spotify.spotify_playlist(url)
                if len(song_list) == 0:
                    await self.send_error_message(ctx=ctx, message=Errors.spotify_pull)
                    return
                for track in song_list:
                    song = Song(song=small_dict)
                    song.title = track
                    small_dicts.append(song)
                _multiple = True
            elif "track" in url:
                track = await self.spotify.spotify_track(url)
                if track is not None:
                    small_dict.title = track.title
                    small_dict.image_url = track.image_url
                    _multiple = False
                else:
                    return
            elif "album" in url:
                song_list = await self.spotify.spotify_album(url)
                for track in song_list:
                    song = Song(song=small_dict)
                    song.title = track
                    small_dicts.append(song)
                _multiple = True
            elif "artist" in url:
                song_list = await self.spotify.spotify_artist(url)
                for track in song_list:
                    song = Song(song=small_dict)
                    song.title = track
                    small_dicts.append(song)
                _multiple = True

        else:
            if url == "charts":
                song_list = await self.spotify.spotify_playlist(
                    "https://open.spotify.com/playlist/37i9dQZEVXbMDoHDwVN2tF?si=vgYiEOfYTL-ejBdn0A_E2g"
                )
                for track in song_list:
                    song = Song(song=small_dict)
                    song.title = track
                    small_dicts.append(song)
                _multiple = True
            else:
                small_dict.title = url
                _multiple = False

        if _multiple:
            for song in small_dicts:
                self.dictionary[ctx.guild.id].song_queue.put_nowait(song)
            await self.send_embed_message(
                ctx=ctx,
                message=":asterisk: Added "
                + str(len(small_dicts))
                + " Tracks to Queue. :asterisk:",
            )
        else:
            if first_index_push:

                self.dictionary[ctx.guild.id].song_queue.queue.appendleft(small_dict)
            else:
                self.dictionary[ctx.guild.id].song_queue.put_nowait(small_dict)
            title = ""
            if small_dict.title is not None:
                title = small_dict.title
            else:
                try:
                    title = small_dict.link
                except AttributeError:
                    pass
            if self.dictionary[ctx.guild.id].voice_client.is_playing():
                if not playskip:
                    await self.send_embed_message(
                        ctx, ":asterisk: Added **" + title + "** to Queue."
                    )

        try:
            if playskip:
                if self.dictionary[ctx.guild.id].voice_client is not None:
                    if self.dictionary[ctx.guild.id].voice_client.is_playing():
                        self.dictionary[ctx.guild.id].voice_client.stop()
            if not self.dictionary[ctx.guild.id].voice_client.is_playing():
                await self.pre_player(ctx)
            await self.preload_song(ctx)
        except Exception as e:
            self.log.error(print(traceback.format_exc()))
            self.log.error(logging_manager.debug_info(str(e)))

    async def join_check(self, ctx, url):
        if url is None:
            await self.send_error_message(ctx, "You need to enter something to play.")
            return False
        if self.dictionary[ctx.guild.id].voice_channel is None:
            if ctx.author.voice is not None:
                self.dictionary[ctx.guild.id].voice_channel = ctx.author.voice.channel
            else:
                await self.send_error_message(ctx, "You need to be in a channel.")
                return False
        if not await self.__same_channel_check(ctx):
            return False
        return True

    async def join_channel(self, ctx):
        if self.dictionary[ctx.guild.id].voice_client is None:
            try:
                if (
                    ctx.author.voice.channel.user_limit
                    <= len(ctx.author.voice.channel.members)
                    and ctx.author.voice.channel.user_limit != 0
                ):
                    if ctx.guild.me.guild_permissions.administrator is True:
                        self.dictionary[
                            ctx.guild.id
                        ].voice_client = await ctx.author.voice.channel.connect(
                            timeout=60, reconnect=True
                        )
                    else:
                        await self.send_embed_message(
                            ctx, "Error while joining your channel. :frowning: (1)"
                        )
                        return False
                else:
                    self.dictionary[
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
                self.log.warning(logging_manager.debug_info("channel_join " + str(e)))
                self.dictionary[ctx.guild.id].voice_channel = None
                await self.send_embed_message(
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
            await self.send_embed_message(ctx, "This is not a valid/supported url.")
            return False
        return True

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        numbers = [
            "`(1)`",
            "`(2)`",
            "`(3)`",
            "`(4)`",
            "`(5)`",
            "`(6)`",
            "`(7)`",
            "`(8)`",
            "`(9)`",
        ]
        use_embeds = environ.get("USE_EMBEDS", "True") == "True"
        no_embed_string = ""
        embed = discord.Embed(colour=0x00FFCC)
        if use_embeds:
            if self.dictionary[ctx.guild.id].now_playing is not None:
                embed.add_field(
                    name="**Currently Playing ...**",
                    value="`" + self.dictionary[ctx.guild.id].now_playing.title + "`\n",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="**Currently Playing...**", value="Nothing.\n", inline=False
                )
        else:
            no_embed_string += "**Currently Playing ...**" + "\n"
            try:
                no_embed_string += (
                    "`" + self.dictionary[ctx.guild.id].now_playing.title + "`\n"
                )
            except AttributeError:
                no_embed_string += "Nothing.\n"

        if len(self.dictionary[ctx.guild.id].song_queue.queue) > 0:
            _t = ""
            for x in range(0, 9, 1):
                try:

                    if self.dictionary[ctx.guild.id].song_queue.queue[x] is not None:

                        _t += (
                            numbers[x]
                            + " `"
                            + self.dictionary[ctx.guild.id].song_queue.queue[x].title
                            + "`\n"
                        )

                    elif (
                        self.dictionary[ctx.guild.id].song_queue.queue[x].link
                        is not None
                    ):

                        _t += (
                            numbers[x]
                            + " `"
                            + self.dictionary[ctx.guild.id].song_queue.queue[x].link
                            + "`\n"
                        )
                    else:
                        break
                except (IndexError, KeyError, AttributeError, TypeError):
                    break

            if (len(self.dictionary[ctx.guild.id].song_queue.queue) - 9) > 0:
                _t += (
                    "`(+)` `"
                    + str(len(self.dictionary[ctx.guild.id].song_queue.queue) - 9)
                    + " Tracks...`"
                )
            if use_embeds:
                embed.add_field(name="**Coming up:**", value=_t, inline=False)
            else:
                no_embed_string += "**Coming up:**\n"
                no_embed_string += _t
        else:
            if use_embeds:
                embed.add_field(
                    name="**Coming up:**",
                    value="Nothing in Queue. Use .play to add something.",
                    inline=False,
                )
            else:
                no_embed_string += "**Coming up:**\n"
                no_embed_string += "Nothing in Queue. Use .play to add something."

        if use_embeds:
            await ctx.send(embed=embed)
        else:
            await ctx.send(content=no_embed_string)

    @commands.command()
    async def rename(self, ctx, *, name: str):
        try:
            if ctx.guild.me.guild_permissions.administrator is False:
                await self.send_error_message(
                    ctx, "You need to be an Administrator to execute this action."
                )
                return
        except AttributeError as ae:
            self.log.error(logging_manager.debug_info("AttributeError " + str(ae)))
        try:
            if len(name) > 32:
                await self.send_error_message(
                    ctx, "Name too long. 32 chars is the limit."
                )
            me = ctx.guild.me
            await me.edit(nick=name)
            await self.send_embed_message(ctx, "Rename to **" + name + "** successful.")
        except Exception as e:
            await self.send_error_message(ctx, "An Error occurred: " + str(e))

    @commands.command(aliases=["v"])
    async def volume(self, ctx, volume=None):
        if not await self.__manipulation_checks(ctx):
            return
        current_volume = await self.mongo.get_volume(ctx.guild.id)
        if volume is None:
            await self.send_embed_message(
                ctx,
                "The current volume is: "
                + str(current_volume)
                + ". It only updates on song changes, so beware.",
            )
            return
        try:
            var = float(volume)
        except ValueError:
            await self.send_error_message(ctx, "You need to enter a number.")
            return
        if var < 0 or var > 2:
            await self.send_error_message(
                ctx, "The number needs to be between 0.0 and 2.0."
            )
            return
        await self.mongo.set_volume(ctx.guild.id, var)
        await self.send_embed_message(ctx, "The Volume was set to: " + str(var))

    @commands.command()
    async def info(self, ctx):
        self.dictionary = self.dictionary
        if self.dictionary[ctx.guild.id].now_playing is None:
            embed = discord.Embed(
                title="Information",
                description="Nothing is playing right now.",
                color=0x00FFCC,
                url="https://d.chulte.de",
            )
            await ctx.send(embed=embed)
            return
        try:
            embed = discord.Embed(
                title="Information",
                description="Name: "
                + str(self.dictionary[ctx.guild.id].now_playing.title)
                + "\nStreamed from: "
                + str(self.dictionary[ctx.guild.id].now_playing.link)
                + "\nDuration: "
                + str(self.dictionary[ctx.guild.id].now_playing.duration)
                + "\nRequested by: <@!"
                + str(self.dictionary[ctx.guild.id].now_playing.user.id)
                + ">\nLoaded in: "
                + str(round(self.dictionary[ctx.guild.id].now_playing.loadtime, 2))
                + " sec."
                + "\nSearched Term: "
                + str(self.dictionary[ctx.guild.id].now_playing.term),
                color=0x00FFCC,
                url="https://d.chulte.de",
            )
            if self.dictionary[ctx.guild.id].now_playing.image is not None:
                embed.set_thumbnail(url=self.dictionary[ctx.guild.id].now_playing.image)
            await ctx.send(embed=embed)
        except (KeyError, TypeError) as e:
            self.log.warning(logging_manager.debug_info(str(e)))
            embed = discord.Embed(
                title="Error",
                description=Errors.info_check,
                url="https://d.chulte.de",
                color=0x00FFCC,
            )
            await ctx.send(embed=embed)

    @commands.command(aliases=["exit"])
    async def quit(self, ctx):
        if not await self.__manipulation_checks(ctx):
            return
        self.dictionary[ctx.guild.id].now_playing = None
        self.dictionary[ctx.guild.id].song_queue = Queue()
        await self.clear_presence(ctx)
        await self.dictionary[ctx.guild.id].voice_client.disconnect()
        self.dictionary[ctx.guild.id].voice_client = None
        await self.send_embed_message(ctx, "Goodbye! :wave:")

    @commands.command(aliases=["empty"])
    async def clear(self, ctx):
        if not await self.__manipulation_checks(ctx):
            return
        if self.dictionary[ctx.guild.id].song_queue.qsize() != 0:
            self.dictionary[ctx.guild.id].song_queue = Queue()
            await self.send_embed_message(ctx, "Cleared the Queue. :cloud:")
        else:
            await self.send_error_message(
                ctx, "The Playlist was already empty! :cloud:"
            )

    @commands.command(aliases=["mixer"])
    async def shuffle(self, ctx):
        if not await self.__manipulation_checks(ctx):
            return
        if self.dictionary[ctx.guild.id].song_queue.qsize() > 0:
            random.shuffle(self.dictionary[ctx.guild.id].song_queue.queue)
            await self.send_embed_message(ctx, "Shuffled! :twisted_rightwards_arrows:")
            await self.preload_song(ctx)
        else:
            await self.send_error_message(ctx, "The queue is empty. :cloud:")

    @commands.command(aliases=["yeehee"])
    async def stop(self, ctx):
        if not await self.__manipulation_checks(ctx):
            return
        if self.dictionary[ctx.guild.id].voice_client is not None:
            self.dictionary[ctx.guild.id].song_queue = Queue()
            self.dictionary[ctx.guild.id].now_playing = None
            self.dictionary[ctx.guild.id].voice_client.stop()
            link = await self.youtube.youtube_url(
                "https://www.youtube.com/watch?v=siLkbdVxntU"
            )
            source = discord.FFmpegPCMAudio(
                link.stream,
                executable="ffmpeg",
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            )
            self.dictionary[ctx.guild.id].voice_client.play(source)
            if (
                self.dictionary[ctx.guild.id].voice_client is not None
                and self.dictionary[ctx.guild.id].voice_client.is_playing()
            ):
                await self.send_embed_message(ctx, "Music Stopped! :octagonal_sign:")
        else:
            await self.send_error_message(
                ctx, ":thinking: The Bot isn't connected. :thinking:"
            )

    @commands.command(aliases=[])
    async def chars(self, ctx, first=None, last=None):
        if first is None:
            full, empty = await self.mongo.get_chars(ctx.guild.id)
            if environ.get("USE_EMBEDS", "True") == "True":
                embed = discord.Embed(
                    title="You are currently using **"
                    + full
                    + "** for 'full' and **"
                    + empty
                    + "** for 'empty'",
                    color=0x00FFCC,
                )
                embed.add_field(
                    name="Syntax to add:",
                    value=".chars <full> <empty> \n"
                    "Useful Website: https://changaco.oy.lc/unicode-progress-bars/",
                )
                await ctx.send(embed=embed)
                return
            message = (
                "You are currently using **"
                + full
                + "** for 'full' and **"
                + empty
                + "** for 'empty'\n"
            )
            message += "Syntax to add:\n"
            message += ".chars <full> <empty> \n"
            message += (
                "Useful Website: https://changaco.oy.lc/unicode-progress-bars/"
            )
            await ctx.send(content=message)

        elif first == "reset" and last is None:
            await self.mongo.set_chars(ctx.guild.id, "█", "░")
            await self.send_embed_message(
                ctx=ctx, message="Characters reset to: Full: **█** and Empty: **░**"
            )
            return

        elif last is None:
            await self.send_error_message(
                ctx=ctx,
                message="You need to provide 2 Unicode Characters separated with a blank space.",
            )
            return
        if len(first) > 1 or len(last) > 1:
            embed = discord.Embed(
                title="The characters have a maximal length of 1.", color=0x00FFCC
            )
            await ctx.send(embed=embed)
            return
        await self.mongo.set_chars(ctx.guild.id, first, last)
        await self.send_embed_message(
            ctx=ctx,
            message="The characters got updated! Full: **"
            + first
            + "**, Empty: **"
            + last
            + "**",
        )

    async def __song_playing_check(self, ctx):
        if self.dictionary[ctx.guild.id].now_playing is None:
            await self.send_error_message(ctx, "Nothing is playing right now!")
            return False
        return True

    @commands.command(aliases=["halteein"])
    async def pause(self, ctx):
        if not await self.__manipulation_checks(ctx):
            return
        if not await self.__song_playing_check(ctx):
            return
        if self.dictionary[ctx.guild.id].voice_client.is_paused():
            await self.send_error_message(ctx, "Already Paused.")
            return
        if self.dictionary[ctx.guild.id].voice_client is not None:
            self.dictionary[ctx.guild.id].voice_client.pause()
            message = await self.send_embed_message(ctx, "Paused! :pause_button:")
            await asyncio.sleep(5)
            await message.delete()
            await ctx.message.delete()

    @commands.command(aliases=["next", "müll", "s", "n"])
    async def skip(self, ctx, count="1"):
        if not await self.__manipulation_checks(ctx):
            return
        try:
            count = int(count)
        except ValueError:
            await self.send_error_message(ctx, "Please provide a valid number.")
            return
        self.dictionary = self.dictionary
        if self.dictionary[ctx.guild.id].voice_client is not None:
            if self.dictionary[ctx.guild.id].now_playing is not None:
                if count == 1:
                    await self.send_embed_message(
                        ctx, "Skipped! :track_next:", delete_after=10
                    )
                    self.dictionary[ctx.guild.id].voice_client.stop()
                elif count < 1:
                    await self.send_error_message(ctx, "Please provide a valid number.")
                    return
                else:
                    if count > self.dictionary[ctx.guild.id].song_queue.qsize():
                        await self.send_embed_message(
                            ctx,
                            "Skipped "
                            + str(self.dictionary[ctx.guild.id].song_queue.qsize())
                            + " Tracks! :track_next:",
                        )
                        self.dictionary[ctx.guild.id].voice_client.stop()
                    else:

                        queue = self.dictionary[ctx.guild.id].song_queue.queue

                        self.dictionary[
                            ctx.guild.id
                        ].song_queue.queue = collections.deque(
                            # noinspection PyPep8
                            list(queue)[(count - 1) :]
                        )
                    self.dictionary[ctx.guild.id].voice_client.stop()
                    await self.send_embed_message(
                        ctx, "Skipped " + str(count) + " Tracks! :track_next:"
                    )
            else:
                await self.send_error_message(
                    ctx, "Nothing is playing right now!", delete_after=10
                )

        else:
            await self.send_error_message(ctx, "Not connected!", delete_after=10)

        await asyncio.sleep(10)
        await ctx.message.delete()

    @commands.command(aliases=["unpause"])
    async def resume(self, ctx):
        if not await self.__manipulation_checks(ctx):
            return
        if not await self.__song_playing_check(ctx):
            return
        if self.dictionary[ctx.guild.id].voice_client is not None:
            if self.dictionary[ctx.guild.id].voice_client.is_paused():
                self.dictionary[ctx.guild.id].voice_client.resume()
                await self.send_embed_message(ctx, "Unpaused! :play_pause:")
            else:
                await self.send_error_message(ctx, "Not Paused.")

    @commands.command()
    async def reset(self, ctx):
        if self.dictionary[ctx.guild.id].voice_client is not None:
            await self.dictionary[ctx.guild.id].voice_client.disconnect()
        if ctx.guild.id not in self.dictionary:
            self.dictionary[ctx.guild.id] = Guild()
        self.dictionary[ctx.guild.id].song_queue = Queue()
        self.dictionary[ctx.guild.id].voice_client = None
        self.dictionary[ctx.guild.id].voice_channel = None
        self.dictionary[ctx.guild.id].now_playing = None
        embed = discord.Embed(
            title="I hope this resolved your issues. :smile: Click me if you want to file a bug report.",
            color=0x00FFCC,
            url="https://github.com/tooxo/Geiler-Musik-Bot/issues/new",
        )
        await ctx.send(embed=embed)
        await self.send_embed_message(
            ctx,
            "I hope this resolved your issues. :smile: Click me if you want to file a bug report.",
        )

    @commands.command()
    async def restart(self, ctx, restart_string=None):
        if restart_string is None:
            embed = discord.Embed(
                title="You need to provide a valid restart key.",
                url="https://d.chulte.de/restart_token",
                color=0x00FFCC,
            )
            await ctx.send(embed=embed)
            return
        correct_string = await self.mongo.get_restart_key()
        if restart_string == correct_string:
            await self.send_embed_message(ctx, "Restarting!")
            await self.bot.logout()
        else:
            embed = discord.Embed(
                title="Wrong token!", url="https://d.chulte.de", color=0x00FFCC
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def eval(self, ctx, *, code: str = None):
        if ctx.author.id != 322807058254528522:
            embed = discord.Embed(title="No permission.", color=0xFF0000)
            await ctx.send(embed=embed)
            return
        try:
            s = str(eval(code))
        except Exception as e:
            s = str(e)
        if len(s) < 256:
            embed = discord.Embed(title=s)
            await ctx.send(embed=embed)
        elif len(s) < 1994:
            sa = "```" + s + "```"
            await ctx.send(sa)
        else:
            sa = "```" + s[:1994] + "```"
            await ctx.send(sa)

    @commands.command(aliases=["np", "nowplaying"])
    async def now_playing(self, ctx):
        songs = []
        for server in self.dictionary:
            if server == ctx.guild.id:
                continue
            server = self.dictionary[server]
            if server.now_playing is not None:
                songs.append(server.now_playing)
        if len(songs) == 0:
            embed = discord.Embed(
                title="Nobody is streaming right now.",
                url="https://d.chulte.de",
                color=0x00FFCC,
            )
            await ctx.send(embed=embed)
            return

        song: Song = random.choice(songs)

        if len(songs) == 1:
            embed = discord.Embed(
                title="`>` `" + song.title + "`",
                description="There is currently 1 Server playing!",
            )
        else:
            embed = discord.Embed(
                title="`>` `" + song.title + "`",
                description="There are currently "
                + str(len(songs))
                + " Servers playing!",
            )
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(DiscordBot(bot))
