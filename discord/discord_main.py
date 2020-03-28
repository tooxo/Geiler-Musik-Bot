import logging
import os
import subprocess
import traceback

import discord
import logging_manager
from bot.discord_music import DiscordBot
from bot.discord_text import TextResponse
from bot.HelpCommand import Help
from bot.type.exceptions import (
    BotNotConnected,
    NoNodeReadyException,
    NothingPlaying,
    NotSameChannel,
    UserNotConnected,
)
from discord.ext import commands
from discord.ext.commands.bot import BotBase

if os.environ.get("TEST_ENVIRONMENT", "False") == "True":

    logging.basicConfig(level=logging.INFO)
    logging.getLogger("discord").setLevel(logging.INFO)

    async def process_commands_n(self, message):
        await self.invoke(await self.get_context(message))

    BotBase.process_commands = process_commands_n
    prefix = ","
else:
    prefix = "."

log = logging_manager.LoggingManager()
log.debug("PID " + str(os.getpid()))

# client = commands.AutoShardedBot(command_prefix=prefix, shard_count=2)
client = commands.Bot(command_prefix=prefix)


def add_cog(cog_type):
    try:
        client.add_cog(cog=cog_type(bot=client))
    except discord.ClientException:
        log.warning(f"{cog_type} was already there, skipped it.")


@client.event
async def on_ready():
    add_cog(DiscordBot)
    add_cog(TextResponse)
    add_cog(Help)
    log.debug("[Startup]: Finished.")
    await client.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, name=".help"
        )
    )


@client.event
async def on_command_error(ctx, error):
    if "not found" in str(error):
        print(error)
    elif "Invalid Data" in str(error):
        await DiscordBot.send_error_message(
            ctx=ctx, message="Error while playback. Try again."
        )
    elif isinstance(error, NotSameChannel):
        await DiscordBot.send_error_message(
            ctx=ctx, message="You need to be in the same channel as the bot."
        )
    elif isinstance(error, UserNotConnected):
        await DiscordBot.send_error_message(
            ctx=ctx, message="You need to be in a channel."
        )
    elif isinstance(error, NothingPlaying):
        await DiscordBot.send_error_message(
            ctx=ctx, message="Nothing is playing."
        )
    elif isinstance(error, BotNotConnected):
        await DiscordBot.send_error_message(
            ctx=ctx, message="The bot isn't connected."
        )
    elif isinstance(error, NoNodeReadyException):
        await DiscordBot.send_error_message(
            ctx=ctx,
            message="Our backend seems to be down right now, try again in a few minutes.",
        )
    elif isinstance(error, discord.ext.commands.MissingRequiredArgument):
        pass
    else:
        log.error(logging_manager.debug_info(str(error)))
        if hasattr(error, "original"):
            traceback.print_tb(error.original.__traceback__)
        else:
            traceback.print_tb(error.__traceback__)


@client.event
async def on_error(*args, **kwargs):
    print(*args, **kwargs)
    traceback.print_exc()


versions = {}
for mod in subprocess.check_output(["pip", "freeze"]).decode().split("\n"):
    if mod:
        versions[mod.split("==")[0]] = mod.split("==")[1]


discord_version = versions["discord.py"]

log.debug("")
log.debug("[Startup]: Using Discord.Py Version " + discord_version)
log.debug("")

log.debug("[Startup]: Starting Up!")

client.run(os.environ.get("BOT_TOKEN", ""))
