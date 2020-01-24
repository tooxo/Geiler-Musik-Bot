import asyncio
import random
import string
from os import environ
from typing import Dict

import dbl
import discord
from discord.ext import commands

import logging_manager
from bot.type.errors import Errors
from bot.type.guild import Guild
from bot.type.song import Song
from bot.voice.checks import Checks
from bot.voice.events import Events
from bot.voice.player import Player
from bot.voice.player_controls import PlayerControls
from extractors import mongo, spotify, youtube, soundcloud


class DiscordBot(commands.Cog):
    def __init__(self, bot):
        self.log = logging_manager.LoggingManager()
        self.log.debug("[Startup]: Initializing Music Module . . .")

        self.dictionary: Dict[Guild] = {}

        self.bot = bot
        self.bot.remove_command("help")

        self.bot.add_cog(Player(self.bot, self))
        self.bot.add_cog(Events(self.bot, self))
        self.bot.add_cog(PlayerControls(self.bot, self))

        self.spotify = spotify.Spotify()
        self.mongo = mongo.Mongo()

        self.youtube = youtube.Youtube(mongo_client=self.mongo)

        restart_key = self.generate_key(64)
        asyncio.run_coroutine_threadsafe(
            self.mongo.set_restart_key(restart_key), self.bot.loop
        )

        # Fix for OpusNotLoaded Error.
        if not discord.opus.is_loaded():
            discord.opus.load_opus("/usr/lib/libopus.so")

        self.control_check = Checks(self.bot, self)

        self.dbl_key = environ.get("DBL_KEY", "")

        # reconnect all pending clients
        self.reconnect()

        # start stats
        self.run_dbl_stats()

    @staticmethod
    def generate_key(length):
        letters = string.ascii_letters
        response = ""
        for _ in range(0, length):
            response += random.choice(letters)
        return response

    @staticmethod
    async def send_embed_message(
        ctx: discord.ext.commands.Context, message: str, delete_after: int = 10
    ):
        if environ.get("USE_EMBEDS", "True") == "True":
            embed = discord.Embed(
                title=message, url="https://d.chulte.de", colour=0x00FFCC
            )
            message = await ctx.send(embed=embed, delete_after=delete_after)
        else:
            message = await ctx.send(message, delete_after=delete_after)
        if delete_after is not None:
            asyncio.ensure_future(DiscordBot.delete_message(ctx.message, delete_after))
        return message

    def reconnect(self):
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

    def run_dbl_stats(self):
        if self.dbl_key != "":
            dbl_client = dbl.DBLClient(self.bot, self.dbl_key)

            async def update_stats(client):
                while not client.bot.is_closed():
                    try:
                        await client.post_guild_count()
                        self.log.debug(
                            "[SERVER COUNT] Posted server count ({})".format(
                                client.guild_count()
                            )
                        )
                        await self.bot.change_presence(
                            activity=discord.Activity(
                                type=discord.ActivityType.listening,
                                name=".help on {} servers".format(client.guild_count()),
                            )
                        )
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
            if self.dictionary[ctx.guild.id].now_playing_message is not None:
                await self.dictionary[ctx.guild.id].now_playing_message.stop()
                try:
                    await ctx.message.delete()
                except discord.NotFound:
                    pass
        except discord.NotFound:
            self.dictionary[ctx.guild.id].now_playing_message = None

    @staticmethod
    async def delete_message(message: discord.Message, delay: int = None):
        try:
            await message.delete(delay=delay)
        except (discord.HTTPException, discord.Forbidden) as e:
            logging_manager.LoggingManager().warning(logging_manager.debug_info(e))

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
        if not await self.control_check.manipulation_checks(ctx):
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
            message += "Useful Website: https://changaco.oy.lc/unicode-progress-bars/"
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
