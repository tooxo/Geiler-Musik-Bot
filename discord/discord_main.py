"""
Main
"""
import logging
import os
import subprocess
import traceback
import typing
from typing import Type

import discord
import logging_manager
from bot.discord_music import DiscordBot
from bot.discord_text import TextResponse
from bot.help_command import Help
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

    # override process_commands to allow bots using commands
    async def _process_commands_n(self, message: discord.Message) -> None:
        await self.invoke(await self.get_context(message))

    BotBase.process_commands = _process_commands_n
    PREFIX = ","
else:
    PREFIX = "."

LOG = logging_manager.LoggingManager()
LOG.debug("PID " + str(os.getpid()))

# client = commands.AutoShardedBot(command_prefix=prefix, shard_count=2)
CLIENT = commands.Bot(command_prefix=PREFIX)


def add_cog(cog_type: Type[typing.Callable]):
    """
    Add a cog
    @param cog_type:
    @return:
    """
    try:
        CLIENT.add_cog(cog=cog_type(bot=CLIENT))
    except discord.ClientException:
        LOG.warning(f"{cog_type} was already there, skipped it.")


@CLIENT.event
async def on_ready() -> None:
    """
    Called when the bot is started.
    @return:
    """
    add_cog(DiscordBot)
    add_cog(TextResponse)
    add_cog(Help)
    LOG.debug("[Startup]: Finished.")
    await CLIENT.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, name=".help"
        )
    )


@CLIENT.event
async def on_command_error(
    ctx: commands.Context, error: Type[Exception]
) -> None:
    """
    Called when an error occurred while processing a command
    @param ctx:
    @param error:
    @return:
    """
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
        LOG.error(logging_manager.debug_info(str(error)))
        if hasattr(error, "original"):
            traceback.print_tb(error.original.__traceback__)
        else:
            traceback.print_tb(error.__traceback__)


@CLIENT.event
async def on_error(*args, **kwargs) -> None:
    """
    Called when a general error occurred
    @param args:
    @param kwargs:
    @return:
    """
    print(*args, **kwargs)
    traceback.print_exc()


VERSIONS = {}
for mod in (
    subprocess.check_output(["/usr/local/bin/pip", "freeze"], shell=False)
    .decode()
    .split("\n")
):
    if mod:
        VERSIONS[mod.split("==")[0]] = mod.split("==")[1]


DISCORD_VERSION = VERSIONS["discord.py"]

LOG.debug("")
LOG.debug("[Startup]: Using Discord.Py Version " + DISCORD_VERSION)
LOG.debug("")

LOG.debug("[Startup]: Starting Up!")

CLIENT.run(os.environ.get("BOT_TOKEN", ""))
