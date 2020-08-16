"""
DiscordMusic
"""
import asyncio
import datetime
import random
import string
from os import environ
from typing import Dict, List, Optional

import dbl
import discord
from discord.ext import commands

import logging_manager
from bot.node_controller.controller import Controller
from bot.type.errors import Errors
from bot.type.exceptions import NoResultsFound
from bot.type.guild import Guild
from bot.type.song import Song
from bot.voice.checks import Checks
from bot.voice.events import Events
from bot.voice.player import Player
from bot.voice.player_controls import PlayerControls
from bot.voice.tts import TTS
from extractors import genius, mongo, soundcloud, spotify, watch2gether, youtube
from bot.voice.player_beta import BetaPlayer


class DiscordBot(commands.Cog, name="Miscellaneous"):
    """
    DiscordBot
    """

    def __init__(self, bot: commands.Bot) -> None:
        self.log = logging_manager.LoggingManager()
        self.log.debug("[Startup]: Initializing Music Module . . .")

        self.guilds: Dict[int, Guild] = {}

        self.bot: commands.Bot = bot
        if environ.get("BETA_PLAYER", "False") == "True":
            self.player: BetaPlayer = BetaPlayer(self.bot, self)
        else:
            self.player: Player = Player(self.bot, self)

        self.bot.add_cog(self.player)
        self.bot.add_cog(Events(self.bot, self))
        self.bot.add_cog(PlayerControls(self.bot, self))
        self.bot.add_cog(TTS(self.bot, self))

        self.node_controller: Controller = Controller(self)
        asyncio.ensure_future(self.node_controller.start_server())

        self.spotify: spotify.Spotify = spotify.Spotify()
        self.mongo: mongo.Mongo = mongo.Mongo()

        self.soundcloud = soundcloud.SoundCloud(
            node_controller=self.node_controller
        )
        self.youtube = youtube.Youtube(node_controller=self.node_controller)

        self.watch2gether = watch2gether.Watch2Gether()

        restart_key = self.generate_key(64)
        asyncio.create_task(self.mongo.set_restart_key(restart_key))

        self.control_check = Checks(self.bot, self)

        self.dbl_key = environ.get("DBL_KEY", "")

        # add all servers to the guilds dict
        self._index()

        # start server count
        self._run_dbl_stats()

    @staticmethod
    def generate_key(length: int) -> str:
        """
        Generates a n character long string of ascii letters
        :param length: length
        :return: key / string
        """
        letters = string.ascii_letters
        response = ""
        for _ in range(0, length):
            response += random.choice(letters)
        return response

    @staticmethod
    async def send_message(
            ctx: commands.Context,
            content: str,
            use_embed: Optional[bool] = False,
            use_citation: Optional[bool] = False,
            use_code_block: Optional[bool] = False,
            delete_after: Optional[int] = None,
            url: Optional[str] = None,
            color: Optional[int] = 0x00FFCC,
    ) -> List[discord.Message]:
        # decide on transfer method
        # embed title = max 256 chars
        # embed description = max 2048 characters
        # common message = max 2000 chars
        messages = []  # all the message sent.
        if use_embed:
            if len(content) <= 256:
                embed: discord.Embed = discord.Embed(
                    title=content, url=url, color=color
                )
                messages.append(
                    await ctx.send(embed=embed, delete_after=delete_after)
                )
                return messages
            while content:
                embed_content = content[:2048]
                content = content[2048:]
                embed: discord.Embed = discord.Embed(
                    description=embed_content, color=color, url=url
                )
                messages.append(
                    await ctx.send(embed=embed, delete_after=delete_after)
                )
            return messages
        if use_citation:
            lines = content.split("\n")
            new_chunk = ""
            partial = ""
            for _line in lines:
                if len(_line) > 1997:
                    _line_container = []
                    while _line:
                        _line_container.append(_line[:1997])
                        _line = _line[
                                1997:
                                ]  # 1997, because the ">" the " " and
                        # the "\n" need to be subtracted.
                else:
                    _line_container = [_line]
                for line in _line_container:
                    new_chunk = ""
                    # in the following I am using a zero-width unicode char
                    # because discord won't format an empty message, so I need
                    # to fill it with something invisible
                    if line in ("", " "):
                        if not new_chunk.endswith(
                                "> \N{MONGOLIAN VOWEL SEPARATOR}\n"
                        ) and (
                                not partial.endswith(
                                    "> \N{MONGOLIAN VOWEL SEPARATOR}\n"
                                )
                                and not new_chunk
                        ):
                            new_chunk += "> \N{MONGOLIAN VOWEL SEPARATOR}\n"
                    else:
                        new_chunk += "> " + line + "\n"
                    if (len(partial) + len(new_chunk)) >= 2000:
                        messages.append(
                            await ctx.send(
                                content=partial, delete_after=delete_after
                            )
                        )
                        partial = new_chunk
                    else:
                        partial += new_chunk
            if partial:
                messages.append(
                    await ctx.send(content=partial, delete_after=delete_after)
                )
            if new_chunk and not partial.endswith(new_chunk):
                messages.append(
                    await ctx.send(content=new_chunk, delete_after=delete_after)
                )
            return messages
        if use_code_block:
            while content:
                message_content = f"```{content[:1993]}```"
                content = content[1993:]
                messages.append(
                    await ctx.send(
                        content=message_content, delete_after=delete_after
                    )
                )
            return messages
        while content:
            message_content = content[:2000]
            content = content[2000:]
            messages.append(
                await ctx.send(
                    content=message_content, delete_after=delete_after
                )
            )
        return messages

    @staticmethod
    async def send_embed_message(
            ctx: discord.ext.commands.Context,
            message: str,
            delete_after: Optional[int] = 10,
            url: str = "https://d.chulte.de",
    ) -> discord.Message:
        """
        Send Embedded messages to a discord text channel
        """
        try:
            if environ.get("USE_EMBEDS", "True") == "True":
                return (
                    await DiscordBot.send_message(
                        ctx=ctx,
                        content=message,
                        delete_after=delete_after,
                        use_embed=True,
                        url=url,
                    )
                )[-1]
            return (
                await DiscordBot.send_message(
                    ctx, message, delete_after=delete_after
                )
            )[-1]
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            raise commands.CommandError("Message forbidden.")

    def _index(self) -> None:
        for _guild in self.bot.guilds:
            _guild: discord.Guild
            self.guilds[_guild.id] = Guild()
            asyncio.ensure_future(
                self.guilds[_guild.id].inflate_from_mongo(self.mongo, _guild.id)
            )

    def _run_dbl_stats(self) -> None:
        if self.dbl_key != "":
            dbl_client = dbl.DBLClient(self.bot, self.dbl_key)

            async def _update_stats(client) -> None:
                last_count = 0
                while not client.bot.is_closed():
                    try:
                        if client.guild_count() != last_count:
                            await client.post_guild_count()
                            self.log.debug(
                                f"[SERVER COUNT] Posted server count "
                                f"({client.guild_count()})"
                            )
                            await self.bot.change_presence(
                                activity=discord.Activity(
                                    type=discord.ActivityType.listening,
                                    name=".help on {} servers".format(
                                        client.guild_count()
                                    ),
                                )
                            )
                            last_count = client.guild_count()
                    except Exception as raised_exception:
                        self.log.warning(
                            logging_manager.debug_info(str(raised_exception))
                        )
                    await asyncio.sleep(1800)

            self.bot.loop.create_task(_update_stats(dbl_client))

    @staticmethod
    async def delete_message(
            message: discord.Message, delay: int = None
    ) -> None:
        """
        Deletes a message with an optional delay
        @param message:
        @param delay:
        @return:
        """
        try:
            await message.delete(delay=delay)
        except (
                discord.HTTPException,
                discord.Forbidden,
                discord.NotFound,
        ) as raised_exceptions:
            logging_manager.LoggingManager().debug(
                logging_manager.debug_info(raised_exceptions)
            )

    @staticmethod
    async def send_error_message(
            ctx: commands.Context, message: str, delete_after: int = 30
    ) -> discord.Message:
        """
        Sends an error message
        :param delete_after:
        :param ctx: bot.py context
        :param message: the message to send
        :return:
        """
        try:
            if environ.get("USE_EMBEDS", "True") == "True":
                return (
                    await DiscordBot.send_message(
                        ctx=ctx,
                        content=message,
                        delete_after=delete_after,
                        use_embed=True,
                        color=0xFF0000,
                    )
                )[-1]
            return (
                await DiscordBot.send_message(
                    ctx=ctx,
                    content=message,
                    delete_after=delete_after,
                    use_embed=False,
                )
            )[-1]

        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            raise commands.CommandError("Message Forbidden.")

    @commands.command()
    async def rename(self, ctx, *, name: str):
        """
        Renames the bot.
        :param ctx:
        :param name:
        :return:
        """
        try:
            if ctx.guild.me.guild_permissions.administrator is False:
                await self.send_error_message(
                    ctx,
                    "You need to be an Administrator to execute this action.",
                )
                return
        except AttributeError as attribute_error:
            self.log.error(
                logging_manager.debug_info(
                    "AttributeError " + str(attribute_error)
                )
            )
        try:
            if len(name) > 32:
                await self.send_error_message(
                    ctx, "Name too long. 32 chars is the limit."
                )
                return
            bot_user = ctx.guild.me
            await bot_user.edit(nick=name)
            await self.send_embed_message(
                ctx, "Rename to **" + name + "** successful."
            )
        except Exception as raised_exception:
            await self.send_error_message(
                ctx, "An Error occurred: " + str(raised_exception)
            )

    @commands.check(Checks.manipulation_checks)
    @commands.command(aliases=["v"])
    async def volume(self, ctx, volume=None) -> None:
        """
        Changes playback volume.
        :param ctx:
        :param volume:
        :return:
        """
        current_volume = getattr(
            self.guilds[ctx.guild.id],
            "volume",
            await self.mongo.get_volume(ctx.guild.id),
        )
        if volume is None:
            await self.send_embed_message(
                ctx, "The current volume is: " + str(current_volume) + "."
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
        self.guilds[ctx.guild.id].volume = var
        try:
            await self.guilds[ctx.guild.id].voice_client.set_volume(var)
        except (AttributeError, TypeError):
            # if pcm source, can be ignored simply
            pass
        await self.send_embed_message(ctx, "The Volume was set to: " + str(var))

    @commands.command(aliases=["i", "information"])
    async def info(self, ctx: commands.Context) -> None:
        """
        Shows song info.
        :param ctx:
        :return:
        """
        use_embeds = environ.get("USE_EMBEDS", "True") == "True"
        if self.guilds[ctx.guild.id].now_playing is None:
            await self.send_error_message(ctx, "Nothing is playing.")
            return
        try:
            song: Song = self.guilds[ctx.guild.id].now_playing
            if not use_embeds:
                await self.send_message(
                    use_citation=True,
                    content=f"**Basic Information**\n"
                            f"Name: `{song.title}`\n"
                            f"Url: `{song.link}`\n"
                            f"Duration: "
                            f"`{datetime.timedelta(seconds=song.duration)}`\n"
                            f"User: `{song.user}`\n"
                            f"Term: `{song.term}`\n\n"
                            f"**Stream Information**\n"
                            f"Successful: `{True}`\n"
                            f"Codec: `{song.codec}`\n"
                            f"Bitrate: `{song.abr} kb/s`",
                    ctx=ctx,
                )
            else:
                embed = discord.Embed(
                    title="Information",
                    color=0x00FFCC,
                    url="https://d.chulte.de",
                )
                embed.add_field(
                    name="Basic Information",
                    inline=False,
                    value=(
                            f"**Name**: `{song.title}`\n"
                            + f"**Url**: `{song.link}`\n"
                            + f"**Duration**: "
                              f"`{datetime.timedelta(seconds=song.duration)}`\n"
                            + f"**User**: `{song.user}`\n"
                            + f"**Term**: `{song.term or song.title}`\n"
                    ),
                )
                embed.add_field(
                    name="Stream Information",
                    inline=False,
                    value=(
                            f"**Successful**: `{True}`\n"
                            + f"**Codec**: `{song.codec}\n`"
                            + f"**Bitrate**: `{song.abr} kb/s`"
                    ),
                )
                if self.guilds[ctx.guild.id].now_playing.image is not None:
                    embed.set_thumbnail(
                        url=self.guilds[ctx.guild.id].now_playing.image
                    )
                await ctx.send(embed=embed)
        except (KeyError, TypeError) as raised_exception:
            self.log.warning(logging_manager.debug_info(str(raised_exception)))
            await self.send_error_message(ctx, Errors.info_check)

    @commands.command(aliases=[])
    async def chars(self, ctx, first=None, last=None) -> None:
        """
        Changes playback bar.
        :param ctx:
        :param first:
        :param last:
        :return:
        """
        if first is None:
            # full, empty = await self.mongo.get_chars(ctx.guild.id)
            full, empty = (
                self.guilds[ctx.guild.id].full,
                self.guilds[ctx.guild.id].empty,
            )
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
                    value=".chars <full> <empty> \nUseful Website: "
                          "https://changaco.oy.lc/unicode-progress-bars/",
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
            self.guilds[ctx.guild.id].full, self.guilds[ctx.guild.id].empty = (
                "█",
                "░",
            )
            await self.send_embed_message(
                ctx=ctx,
                message="Characters reset to: Full: **█** and Empty: **░**",
            )
            return

        elif last is None:
            await self.send_error_message(
                ctx=ctx,
                message="You need to provide 2 Unicode Characters "
                        "separated with a blank space.",
            )
            return
        if len(first) > 1 or len(last) > 1:
            embed = discord.Embed(
                title="The characters have a maximal length of 1.",
                color=0x00FFCC,
            )
            await ctx.send(embed=embed)
            return
        await self.mongo.set_chars(ctx.guild.id, first, last)
        self.guilds[ctx.guild.id].full, self.guilds[ctx.guild.id].empty = (
            first,
            last,
        )
        await self.send_embed_message(
            ctx=ctx,
            message="The characters got updated! Full: **"
                    + first
                    + "**, Empty: **"
                    + last
                    + "**",
        )

    @commands.command(hidden=True)
    async def restart(  # pragma: no cover
            self, ctx, restart_string=None
    ) -> None:  # pragma: no cover
        """
        Hidden DEBUG Command
        @param ctx:
        @param restart_string:
        @return:
        """
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

    # noinspection PyUnusedLocal
    @commands.command(hidden=True)
    async def eval(self, ctx, *, code: str = None) -> None:  # pragma: no cover
        """
        Hidden DEBUG Method
        @param ctx:
        @param code:
        @return:
        """
        guild_id = ctx.guild.id
        queue = self.guilds[guild_id].song_queue
        guild = self.guilds[guild_id]
        now_playing = self.guilds[guild_id].now_playing
        now_playing_message = self.guilds[guild_id].now_playing_message
        if ctx.author.id != 322807058254528522:
            embed = discord.Embed(title="No permission.", color=0xFF0000)
            await ctx.send(embed=embed)
            return
        try:
            eval_response = str(eval(code))  # pylint: disable=eval-used
        except Exception as raised_exception:
            eval_response = str(raised_exception)
        await self.send_message(
            content=eval_response, ctx=ctx, use_code_block=True
        )

    @commands.command(hidden=True)
    async def exec(self, ctx, *, code: str = None) -> None:  # pragma: no cover
        """
        Hidden DEBUG Method
        @param ctx:
        @param code:
        @return:
        """
        if ctx.author.id != 322807058254528522:
            embed = discord.Embed(title="No permission.", color=0x00FF0000)
            await ctx.send(embed=embed)
            return
        try:
            exec_response = exec(code)  # pylint: disable=exec-used
        except (Exception, RuntimeWarning) as raised_exception:
            exec_response = str(raised_exception)
        if not exec_response:
            embed = discord.Embed(title="None")
            await ctx.send(embed=embed)
            return
        await self.send_message(ctx, exec_response)

    @commands.command(aliases=["np", "nowplaying"])
    async def now_playing(self, ctx: commands.Context) -> None:
        """
        Shows what other servers are playing.
        :param ctx:
        :return:
        """
        songs = []
        for server in self.guilds:
            if server == ctx.guild.id:
                continue
            server = self.guilds[server]
            if server.now_playing is not None:
                songs.append(server.now_playing)
        if len(songs) == 0:
            await self.send_error_message(ctx, "Nobody is streaming right now.")
            return

        song: Song = random.choice(songs)

        if environ.get("USE_EMBEDS", "True") == "True":
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
        else:
            if len(songs) == 1:
                await self.send_embed_message(
                    ctx,
                    f"`>` `{song.title}`\n"
                    f"There is currently 1 Server playing!",
                )
            else:
                await self.send_embed_message(
                    ctx,
                    f"`>` `{song.title}`"
                    f"There are currently {str(len(songs))} Servers playing!",
                )

    @commands.check(Checks.song_playing_check)
    @commands.command(aliases=["a", "art"])
    async def albumart(self, ctx) -> None:
        """
        Displays the album art.
        :param ctx:
        :return:
        """
        if environ.get("USE_EMBEDS", "True") == "True":
            embed: discord.Embed = discord.Embed(
                title=self.guilds[ctx.guild.id].now_playing.title
            )
            embed.set_image(url=self.guilds[ctx.guild.id].now_playing.image)
            await ctx.send(embed=embed)
        else:
            await self.send_embed_message(
                ctx, self.guilds[ctx.guild.id].now_playing.image
            )

    @commands.command(aliases=["lyric", "songtext", "text"])
    async def lyrics(self, ctx: commands.Context, *, song_name: str = None):
        """
        Displays the lyrics.
        :param ctx:
        :param song_name: The name of the Song, Optional
        :return:
        """
        url = None
        await ctx.channel.trigger_typing()
        if song_name:
            try:
                url = await genius.Genius.search_genius(song_name, "")
            except NoResultsFound:
                return await self.send_error_message(
                    ctx, Errors.no_results_found
                )
            except asyncio.TimeoutError:
                return await self.send_error_message(
                    ctx, Errors.cant_reach_genius
                )
        elif hasattr(self.guilds.get(ctx.guild.id, None), "now_playing"):
            if isinstance(self.guilds[ctx.guild.id].now_playing, Song):
                song: Song = self.guilds[ctx.guild.id].now_playing
                if hasattr(song, "song_name") and hasattr(song, "artist"):
                    if song.song_name is not None and song.artist is not None:
                        url = await genius.Genius.search_genius(
                            song.song_name.replace("(", "").replace(")", ""),
                            song.artist.replace("(", "").replace(")", ""),
                        )
                    else:
                        url = await genius.Genius.search_genius(song.title, "")
        if url:
            try:
                lyrics, header = await genius.Genius.extract_from_genius(url)
            except asyncio.TimeoutError:
                return await self.send_error_message(
                    ctx, Errors.cant_reach_genius
                )
            await ctx.send(content=f"> **{header}**")
            return (await self.send_message(ctx, lyrics, use_citation=True))[
                -1
            ]
        return await self.send_error_message(
            ctx, "Currently not supported for this song."
        )

    @commands.command(aliases=["search"])
    async def service(self, ctx: commands.Context, new_num: str = None) -> None:
        """
        Select the provider used for search.
        @param ctx:
        @param new_num:
        @return:
        """

        async def _set_service(
                _type: str, name: str, _message: discord.Message = None
        ) -> None:
            await self.mongo.set_service(ctx.guild.id, _type)
            await self.send_embed_message(
                ctx, f'Set search provider to "{name}"'
            )
            if _message:
                await self.delete_message(_message)

        if new_num and new_num in ["1", "2", "3"]:
            if new_num == "1":
                self.guilds[ctx.guild.id].search_service = "basic"
                await _set_service("basic", "YouTube Search")
            elif new_num == "2":
                self.guilds[ctx.guild.id].search_service = "music"
                await _set_service("music", "YouTube Music")
            elif new_num == "3":
                self.guilds[ctx.guild.id].search_service = "soundcloud"
                await _set_service("soundcloud", "SoundCloud")
            return

        embed = discord.Embed(title="Select Search Provider")
        if self.guilds[ctx.guild.id].service == "music":
            embed.add_field(
                name="Available Services",
                value="_`1) YouTube Search`_\n"
                      "**`2) YouTube Music Search`**\n_`3) SoundCloud Search`_",
            )
        elif self.guilds[ctx.guild.id].service == "basic":
            embed.add_field(
                name="Available Services",
                value="**`1) YouTube Search`**\n"
                      "_`2) YouTube Music Search`_\n_`3) SoundCloud Search`_",
            )
        else:
            embed.add_field(
                name="Available Services",
                value="_`1) YouTube Search`_\n"
                      "_`2) YouTube Music Search`_\n**`3) SoundCloud Search`**",
            )
        message: discord.Message = await ctx.send(embed=embed)
        await message.add_reaction(
            "\N{Digit One}\N{Combining Enclosing Keycap}"
        )
        await message.add_reaction(
            "\N{Digit Two}\N{Combining Enclosing Keycap}"
        )
        await message.add_reaction(
            "\N{Digit Three}\N{Combining Enclosing Keycap}"
        )

        def _check(reaction: discord.Reaction, user: discord.Member):
            if reaction.message.id == message.id:
                if user.id != self.bot.user.id:
                    if (
                            reaction.emoji
                            == "\N{Digit One}\N{Combining Enclosing Keycap}"
                    ):
                        self.guilds[ctx.guild.id].search_service = "basic"
                        asyncio.ensure_future(
                            _set_service("basic", "YouTube Search", message)
                        )
                        return True
                    if (
                            reaction.emoji
                            == "\N{Digit Two}\N{Combining Enclosing Keycap}"
                    ):
                        self.guilds[ctx.guild.id].search_service = "music"
                        asyncio.ensure_future(
                            _set_service("music", "YouTube Music", message)
                        )
                        return True
                    if (
                            reaction.emoji
                            == "\N{Digit Three}\N{Combining Enclosing Keycap}"
                    ):
                        self.guilds[ctx.guild.id].search_service = "soundcloud"
                        asyncio.ensure_future(
                            _set_service("soundcloud", "SoundCloud", message)
                        )
                        return True
            return False

        async def _reaction_manager() -> None:
            try:
                await self.bot.wait_for(
                    "reaction_add", timeout=60, check=_check
                )
            except asyncio.TimeoutError:
                return

        asyncio.ensure_future(_reaction_manager())

    @commands.command(aliases=["watch2gether", "watchtogether"])
    async def w2g(self, ctx) -> None:
        """
        Creates a Watch2Gether Room
        :param ctx:
        :return:
        """
        url = await self.watch2gether.create_new_room()
        await self.send_embed_message(ctx, url, url=url, delete_after=None)
