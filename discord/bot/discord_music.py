import asyncio
import datetime
import random
import string
import sys
from os import environ
from typing import Dict, Optional

import dbl
import discord
from discord.ext import commands

import logging_manager
from bot.node_controller.controller import Controller
from bot.type.errors import Errors
from bot.type.guild import Guild
from bot.type.song import Song
from bot.voice.checks import Checks
from bot.voice.events import Events
from bot.voice.player import Player
from bot.voice.player_controls import PlayerControls
from bot.voice.tts import TTS
from extractors import genius, mongo, soundcloud, spotify, watch2gether, youtube


class DiscordBot(commands.Cog, name="Miscellaneous"):
    def __init__(self, bot: commands.Bot):
        self.log = logging_manager.LoggingManager()
        self.log.debug("[Startup]: Initializing Music Module . . .")

        self.guilds: Dict[Guild] = {}

        self.bot: commands.Bot = bot
        self.player = Player(self.bot, self)

        self.bot.add_cog(self.player)
        self.bot.add_cog(Events(self.bot, self))
        self.bot.add_cog(PlayerControls(self.bot, self))
        self.bot.add_cog(TTS(self.bot, self))

        self.node_controller = Controller(self)
        asyncio.ensure_future(self.node_controller.start_server())

        self.spotify = spotify.Spotify()
        self.mongo = mongo.Mongo()

        self.soundcloud = soundcloud.SoundCloud(
            node_controller=self.node_controller
        )
        self.youtube = youtube.Youtube(node_controller=self.node_controller)

        self.watch2gether = watch2gether.Watch2Gether()

        restart_key = self.generate_key(64)
        asyncio.create_task(self.mongo.set_restart_key(restart_key))

        # Fix for OpusNotLoaded Error.
        if not discord.opus.is_loaded():
            # this is the default opus installation on ubuntu / debian
            discord.opus.load_opus("/usr/lib/x86_64-linux-gnu/libopus.so")

        self.control_check = Checks(self.bot, self)

        self.dbl_key = environ.get("DBL_KEY", "")

        # disconnects all pending clients
        self.disconnect()

        # start server count
        self.run_dbl_stats()

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
    async def send_embed_message(
        ctx: discord.ext.commands.Context,
        message: str,
        delete_after: Optional[int] = 10,
        url: str = "https://d.chulte.de",
    ) -> discord.Message:
        try:
            if environ.get("USE_EMBEDS", "True") == "True":
                embed = discord.Embed(title=message, url=url, colour=0x00FFCC)
                message = await ctx.send(embed=embed, delete_after=delete_after)
            else:
                message = await ctx.send(message, delete_after=delete_after)
            return message
        except discord.Forbidden:
            raise commands.CommandError("Message forbidden.")

    def disconnect(self):
        for _guild in self.bot.guilds:
            self.guilds[_guild.id] = Guild()
            asyncio.ensure_future(
                self.guilds[_guild.id].inflate_from_mongo(self.mongo, _guild.id)
            )
            try:
                if _guild.me.voice is not None:
                    if hasattr(_guild.me.voice, "channel"):

                        async def reconnect(_guild):
                            """
                            Reconnects disconnected clients after restart
                            :param _guild: guild
                            :return:
                            """
                            self.log.debug(
                                "[Disconnect] Disconnecting " + str(_guild)
                            )
                            t = await _guild.me.voice.channel.connect(
                                timeout=5, reconnect=False
                            )
                            await t.disconnect(force=True)

                        asyncio.run_coroutine_threadsafe(
                            reconnect(_guild), self.bot.loop
                        )
            except AttributeError:
                self.log.warning(f"Failed disconnect for ID: {_guild.id}")

    def run_dbl_stats(self):
        if self.dbl_key != "":
            dbl_client = dbl.DBLClient(self.bot, self.dbl_key)

            async def update_stats(client):
                last_count = 0
                while not client.bot.is_closed():
                    try:
                        if client.guild_count() != last_count:
                            await client.post_guild_count()
                            self.log.debug(
                                "[SERVER COUNT] Posted server count ({})".format(
                                    client.guild_count()
                                )
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
                    except Exception as e:
                        self.log.warning(logging_manager.debug_info(e))
                    await asyncio.sleep(1800)

            self.bot.loop.create_task(update_stats(dbl_client))

    async def clear_presence(self, ctx: discord.ext.commands.Context):
        """
        Stops message updating after a song finished
        :param ctx:
        :return:
        """
        try:
            if self.guilds[ctx.guild.id].now_playing_message is not None:
                await self.guilds[ctx.guild.id].now_playing_message.stop()
                try:
                    await ctx.message.delete()
                except discord.NotFound:
                    pass
        except discord.NotFound:
            self.guilds[ctx.guild.id].now_playing_message = None

    @staticmethod
    async def delete_message(message: discord.Message, delay: int = None):
        try:
            await message.delete(delay=delay)
        except (discord.HTTPException, discord.Forbidden) as e:
            logging_manager.LoggingManager().warning(
                logging_manager.debug_info(e)
            )

    @staticmethod
    async def send_error_message(ctx, message, delete_after=30):
        """
        Sends an error message
        :param delete_after:
        :param ctx: bot.py context
        :param message: the message to send
        :return:
        """
        if environ.get("USE_EMBEDS", "True") == "True":
            embed = discord.Embed(description=message, color=0xFF0000)
            await ctx.send(embed=embed, delete_after=delete_after)
        else:
            await ctx.send(message, delete_after=delete_after)
        if delete_after is not None:
            await DiscordBot.delete_message(ctx.message, delete_after)

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
        except AttributeError as ae:
            self.log.error(
                logging_manager.debug_info("AttributeError " + str(ae))
            )
        try:
            if len(name) > 32:
                await self.send_error_message(
                    ctx, "Name too long. 32 chars is the limit."
                )
            me = ctx.guild.me
            await me.edit(nick=name)
            await self.send_embed_message(
                ctx, "Rename to **" + name + "** successful."
            )
        except Exception as e:
            await self.send_error_message(ctx, "An Error occurred: " + str(e))

    @commands.check(Checks.manipulation_checks)
    @commands.command(aliases=["v"])
    async def volume(self, ctx, volume=None):
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
            self.guilds[ctx.guild.id].voice_client.set_volume(var)
        except (AttributeError, TypeError):
            # if pcm source, can be ignored simply
            pass
        await self.send_embed_message(ctx, "The Volume was set to: " + str(var))

    @commands.command(aliases=["i", "information"])
    async def info(self, ctx):
        """
        Shows song info.
        :param ctx:
        :return:
        """
        self.guilds = self.guilds
        if self.guilds[ctx.guild.id].now_playing is None:
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
                title="Information", color=0x00FFCC, url="https://d.chulte.de"
            )
            song: Song = self.guilds[ctx.guild.id].now_playing
            embed.add_field(
                name="Basic Information",
                inline=False,
                value=(
                    f"**Name**: `{song.title}`\n"
                    + f"**Url**: `{song.link}`\n"
                    + f"**Duration**: `{datetime.timedelta(seconds=song.duration)}`\n"
                    + f"**User**: `{song.user}`\n"
                    + f"**Term**: `{song.term}`\n"
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
        except (KeyError, TypeError) as e:
            self.log.warning(logging_manager.debug_info(str(e)))
            embed = discord.Embed(
                title="Error",
                description=Errors.info_check,
                url="https://d.chulte.de",
                color=0x00FFCC,
            )
            await ctx.send(embed=embed)

    @commands.command(aliases=[])
    async def chars(self, ctx, first=None, last=None):
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
                message="You need to provide 2 Unicode Characters separated with a blank space.",
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

    @commands.command(hidden=True)
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

    @commands.command(hidden=True)
    async def exec(self, ctx, *, code: str = None):
        if ctx.author.id != 322807058254528522:
            embed = discord.Embed(title="No permission.", color=0x00FF0000)
            await ctx.send(embed=embed)
            return
        try:
            s = exec(code)  # pylint: disable=exec-used
        except (Exception, RuntimeWarning) as e:
            s = str(e)
        if not s:
            embed = discord.Embed(title="None")
            await ctx.send(embed=embed)
            return
        if len(s) < 256:
            embed = discord.Embed(title=s)
            await ctx.send(embed=embed)
        elif len(s) < 1994:
            sa = "```" + s + "```"
            await ctx.send(sa)
        else:
            sa = "```" + s[:1994] + "```"
            await ctx.send(sa)

    @commands.command(aliases=["np", "now_playing"])
    async def nowplaying(self, ctx):
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

    @commands.check(Checks.song_playing_check)
    @commands.command(aliases=["a", "art"])
    async def albumart(self, ctx):
        """
        Displays the album art.
        :param ctx:
        :return:
        """
        return await ctx.send(self.guilds[ctx.guild.id].now_playing.image)

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
            url = await genius.Genius.search_genius(song_name, "")
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
            lyrics, header = await genius.Genius.extract_from_genius(url)
            lines = lyrics.split("\n")
            await ctx.send(content=f"> **{header}**")
            t = ""
            for line in lines:
                if (len(t) + len(line)) > 1900:
                    await ctx.send(content=t)
                    t = ""
                if line in ("", " "):
                    if not t.endswith("> \N{MONGOLIAN VOWEL SEPARATOR}\n"):
                        t += (
                            "> \N{MONGOLIAN VOWEL SEPARATOR}\n"
                        )  # the good ol' mongolian vowel separator
                else:
                    t += "> " + line + "\n"
            return await ctx.send(content=t)
        return await self.send_error_message(
            ctx, "Currently not supported for this song."
        )

    @commands.command(aliases=["search"])
    async def service(self, ctx):
        """
        Select the provider used for search.
        :param ctx:
        :return:
        """
        embed = discord.Embed(title="Select Search Provider")
        if self.guilds[ctx.guild.id].service == "music":
            embed.add_field(
                name="Available Services",
                value="_`1) YouTube Search`_\n" "**`2) YouTube Music Search`**",
            )
        else:
            embed.add_field(
                name="Available Services",
                value="**`1) YouTube Search`**\n" "_`2) YouTube Music Search`_",
            )
        message: discord.Message = await ctx.send(embed=embed)
        await message.add_reaction(
            "\N{Digit One}\N{Combining Enclosing Keycap}"
        )
        await message.add_reaction(
            "\N{Digit Two}\N{Combining Enclosing Keycap}"
        )

        def check(reaction: discord.Reaction, user: discord.Member):
            async def set_service(_type, name):
                await self.mongo.set_service(ctx.guild.id, _type)
                await self.send_embed_message(
                    ctx, f'Set search provider to "{name}"'
                )
                await message.delete()

            if reaction.message.id == message.id:
                if user.id != self.bot.user.id:
                    if (
                        reaction.emoji
                        == "\N{Digit One}\N{Combining Enclosing Keycap}"
                    ):
                        self.guilds[ctx.guild.id].search_service = "basic"
                        asyncio.ensure_future(
                            set_service("basic", "YouTube Search")
                        )
                        return True
                    if (
                        reaction.emoji
                        == "\N{Digit Two}\N{Combining Enclosing Keycap}"
                    ):
                        self.guilds[ctx.guild.id].search_service = "music"
                        asyncio.ensure_future(
                            set_service("music", "YouTube Music")
                        )
                        return True
            return False

        async def reaction_manager():
            try:
                await self.bot.wait_for("reaction_add", timeout=60, check=check)
            except asyncio.TimeoutError:
                return

        asyncio.ensure_future(reaction_manager())

    @commands.command(aliases=["w2g", "watchtogether"])
    async def watch2gether(self, ctx):
        """
        Creates a Watch2Gether Room
        :param ctx:
        :return:
        """
        url = await self.watch2gether.create_new_room()
        return await self.send_embed_message(
            ctx, url, url=url, delete_after=None
        )
