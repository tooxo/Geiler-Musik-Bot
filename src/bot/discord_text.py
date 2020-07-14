"""
Text
"""
import discord
from discord.ext import commands

import logging_manager


class TextResponse(commands.Cog, name="Support"):
    """
    Text
    """

    def __init__(self, bot: commands.Bot):
        self.log = logging_manager.LoggingManager()
        self.log.debug("[Startup]: Initializing Text Module . . .")
        self.bot = bot

    @commands.command(aliases=["clemi", "god", "gott"], hidden=True)
    async def cool(self, ctx: commands.Context) -> None:
        """

        @param ctx:
        @return:
        """
        await ctx.send(
            "https://cdn.discordapp.com/attachments/"
            "357956193093812234/563063266457288714/Unbenanntw2.jpg"
        )

    @commands.command(hidden=True)
    async def dani(self, ctx: commands.Context) -> None:
        """

        @param ctx:
        @return:
        """
        await ctx.send(
            "https://media.discordapp.net/attachments/"
            "357956193093812234/566737035541610526/"
            "i_actually_wann_die2.png?width=510&height=676"
        )

    @commands.command(hidden=True)
    async def anstalt(self, ctx: commands.Context) -> None:
        """

        @param ctx:
        @return:
        """
        await ctx.send(
            "https://media.discordapp.net/attachments/"
            "357956193093812234/566329884386000896/HTL.png"
        )

    @commands.command(hidden=True)
    async def niki(self, ctx: commands.Context) -> None:
        """

        @param ctx:
        @return:
        """
        await ctx.send(
            "https://cdn.discordapp.com/attachments/"
            "561858486430859266/563436218914701322/Niki_Nasa.png"
        )

    # // //#
    # INFO ABOUT FUNCTION AND VERSION #
    # // //#

    @commands.command()
    async def support(self, ctx: commands.Context) -> None:
        """
        Shows all supported services.
        :param ctx:
        :return:
        """
        embed = (
            discord.Embed(
                title="Supported Services",
                color=0x00FFCC,
                url="https://d.chulte.de",
            )
            .add_field(
                name="YouTube",
                value="Video Urls\nVideo Search Terms\nPlaylist Urls",
            )
            .add_field(
                name="Spotify",
                value="Track Links\nAlbum Links\nArtist Top-Tracks\nPlaylists",
            )
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["error"])
    async def issue(self, ctx: commands.Context) -> None:
        """
        BugTracker
        :param ctx:
        :return:
        """
        embed = (
            discord.Embed(
                title="Found a bug?",
                color=0x00FFCC,
                url="https://github.com/tooxo/Geiler-Musik-Bot/issues",
            )
            .add_field(
                name="What should I do?",
                value="Create a new Issue or responde to an existing one, describing your issue.",
            )
            .add_field(
                name="Link?",
                value="https://github.com/tooxo/Geiler-Musik-Bot/issues\n"
                "https://github.com/tooxo/Geiler-Musik-Bot/issues/new",
            )
        )
        await ctx.send(embed=embed)
