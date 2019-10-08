from discord.ext import commands
import os
import logging_manager
import logging
from discord.ext.commands.bot import BotBase
import discord
import youtube_dl

if os.environ.get("TEST_ENVIRONMENT", "False") == "True":

    async def process_commands_n(self, message):
        """|coro|
        This function processes the commands that have been registered
        to the bot and other groups. Without this coroutine, none of the
        commands will be triggered.
        By default, this coroutine is called inside the :func:`.on_message`
        event. If you choose to override the :func:`.on_message` event, then
        you should invoke this coroutine as well.
        This is built using other low level tools, and is equivalent to a
        call to :meth:`~.Bot.get_context` followed by a call to :meth:`~.Bot.invoke`.
        This also checks if the message's author is a bot and doesn't
        call :meth:`~.Bot.get_context` or :meth:`~.Bot.invoke` if so.
        Parameters
        -----------
        message: :class:`discord.Message`
            The message to process commands for.
        """
        # if message.author.bot:
        #    return

        ctx = await self.get_context(message)
        await self.invoke(ctx)

    BotBase.process_commands = process_commands_n
    prefix = ","
else:
    prefix = "."

log = logging_manager.LoggingManager()
log.debug("PID " + str(os.getpid()))
# client = commands.AutoShardedBot(command_prefix=prefix, shard_count=2)
client = commands.Bot(command_prefix=prefix)


@client.event
async def on_ready():
    client.load_extension("discord_music")
    client.load_extension("discord_text")
    log.debug("[Startup]: Finished.")
    await client.change_presence(
        activity=discord.Activity(type=discord.ActivityType.listening, name=".help")
    )


@client.event
async def on_command_error(ctx, error):
    if "not found" in str(error):
        embed = discord.Embed(
            title=str(error),
            color=0x00FFCC,
            url="https://github.com/tooxo/Geiler-Musik-Bot/issues",
        )
        await ctx.send(embed=embed)
    elif "Invalid Data" in str(error):
        embed = discord.Embed(
            title="Error while playback. Try again.",
            color=0x00FFCC,
            url="https://github.com/tooxo/Geiler-Musik-Bot/issues",
        )
        await ctx.send(embed=embed)
    else:
        log.error(logging_manager.debug_info(str(error)))


@client.event
async def on_error(error):
    print("ERROR HANDLER", error)


discord_version = discord.__version__ + "-" + discord.version_info.releaselevel
youtube_version = youtube_dl.version.__version__

log.debug("")
log.debug("[Startup]: Using Discord.Py Version " + discord_version)
log.debug("[Startup]: Using Youtube_DL Version " + youtube_version)
log.debug("")

log.debug("[Startup]: Starting Up!")
client.run(os.environ.get("BOT_TOKEN", ""))
