import discord
from discord.ext import commands

class TextResponse(commands.Cog):

    def __init__(self, bot):
        print("[Startup]: Initializing Text Module . . .")
        self.bot = bot

    @commands.command(aliases=["clemi", "god", "gott"])
    async def cool(self, ctx):
        await ctx.send("https://cdn.discordapp.com/attachments/357956193093812234/563063266457288714/Unbenanntw2.jpg")

    @commands.command()
    async def dani(self, ctx):
        await ctx.send("https://media.discordapp.net/attachments/357956193093812234/566737035541610526/i_actually_wann_die2.png?width=510&height=676")

    @commands.command()
    async def anstalt(self, ctx):
        await ctx.send("https://media.discordapp.net/attachments/357956193093812234/566329884386000896/HTL.png")

    @commands.command()
    async def niki(self, ctx):
        await ctx.send("https://cdn.discordapp.com/attachments/561858486430859266/563436218914701322/Niki_Nasa.png")


    @commands.command()
    async def help(self, ctx):
        embed=discord.Embed(title="Help", color=0x00ffcc, url="https://f.chulte.de")\
        .add_field(name="Music Commands", value=".play [songname/link] - Plays a song, Spotify and YouTube are supported. \n.stop - Stops the Playback \n.pause - Pauses the Music \n.resume - Resumes the music \n.shuffle - Shuffles the Queue \n.queue - Shows the coming up songs. \n.volume <num between 0.0 and 2.0> - Changes the playback volume, only updates on song changes.", inline=False)\
        .add_field(name="Debug Commands", value=".np - More infos about the currently playing song\n.ping - Shows the bot's ping \n.echo - [text] - Echoes the text back.\n.rename [name] - Renames the Bot", inline=False)\
        .set_footer(text="despacito")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(TextResponse(bot))
