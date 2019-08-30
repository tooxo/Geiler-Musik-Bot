import discord
from discord.ext import commands
import logging_manager


class TextResponse(commands.Cog):
    def __init__(self, bot):
        self.log = logging_manager.LoggingManager()
        self.log.debug("[Startup]: Initializing Text Module . . .")
        self.bot = bot

    @commands.command(aliases=["clemi", "god", "gott"])
    async def cool(self, ctx):
        await ctx.send("https://cdn.discordapp.com/attachments/357956193093812234/563063266457288714/Unbenanntw2.jpg")

    @commands.command()
    async def dani(self, ctx):
        await ctx.send(
            "https://media.discordapp.net/attachments/357956193093812234/566737035541610526/i_actually_wann_die2.png?width=510&height=676"
        )

    @commands.command()
    async def anstalt(self, ctx):
        await ctx.send("https://media.discordapp.net/attachments/357956193093812234/566329884386000896/HTL.png")

    @commands.command()
    async def niki(self, ctx):
        await ctx.send("https://cdn.discordapp.com/attachments/561858486430859266/563436218914701322/Niki_Nasa.png")

    @commands.command()
    async def help(self, ctx):
        embed = (
            discord.Embed(title="Help", color=0x00FFCC, url="https://d.chulte.de")
            .add_field(
                name="Music Commands",
                value=".play [songname/link] - Plays a song, Spotify and YouTube are supported. \n.stop - Stops the Playback \n.pause - Pauses the Music \n.resume - Resumes the music \n.shuffle - Shuffles the Queue \n.queue - Shows the coming up songs. \n.volume <num between 0.0 and 2.0> - Changes the playback volume, only updates on song changes. \n.chars <full> <empty> - Changes the characters of the progress-bar.",
                inline=False,
            )
            .add_field(
                name="Debug Commands",
                value=".ping - Shows the bot's ping \n.echo - [text] - Echoes the text back.\n.rename [name] - Renames the Bot",
                inline=False,
            )
            .add_field(
                name="Version Commands", value=".support - Shows the supported services\n.issue - File a bug report."
            )
            .set_footer(text="despacito")
        )
        await ctx.send(embed=embed)

    # // //#
    # INFO ABOUT FUNCTION AND VERSION #
    # // //#

    @commands.command()
    async def support(self, ctx):
        embed = (
            discord.Embed(title="Supported Services", color=0x00FFCC, url="https://d.chulte.de")
            .add_field(name="YouTube", value="Video Urls\nVideo Search Terms\nPlaylist Urls")
            .add_field(name="Spotify", value="Track Links\nAlbum Links\nArtist Top-Tracks\nPlaylists")
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["error"])
    async def issue(self, ctx):
        embed = (
            discord.Embed(title="Found a bug?", color=0x00FFCC, url="https://github.com/tooxo/Geiler-Musik-Bot/issues")
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


def setup(bot):
    bot.add_cog(TextResponse(bot))
