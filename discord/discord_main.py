import logging
import os
import subprocess
import traceback

import discord
import youtube_dl
from discord.ext import commands
from discord.ext.commands.bot import BotBase

import logging_manager
from bot.discord_music import DiscordBot
from bot.discord_text import TextResponse
from bot.HelpCommand import Help
from bot.type.exceptions import (
    BotNotConnected,
    NothingPlaying,
    NotSameChannel,
    UserNotConnected,
)

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

# Checking for dependency updates inside the container.
# Currently only updating discord.py and youtube-dl as they are the most important for it to work

log.debug(" ")
log.debug("[Update]: Checking for library updates!")

command = [
    "/usr/local/bin/pip",
    "install",
    "--upgrade",
    "discord.py",
    "youtube-dl",
]
response = subprocess.check_output(command, shell=False).decode()

# Check if an update has occurred
if "Successfully installed" in response:
    log.debug("[Update]: Updates installed. Restarting!")
    # Trigger a reboot
    raise SystemExit("Restarting...")
log.debug("[Update]: No update found. Starting normally.")

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
    elif isinstance(error, discord.ext.commands.MissingRequiredArgument):
        pass
    else:
        log.error(logging_manager.debug_info(str(error)))
        traceback.print_tb(error.original.__traceback__)


@client.event
async def on_error(*args, **kwargs):
    print(*args, **kwargs)
    traceback.print_exc()


discord_version = discord.__version__ + "-" + discord.version_info.releaselevel
youtube_version = youtube_dl.version.__version__

log.debug("")
log.debug("[Startup]: Using Discord.Py Version " + discord_version)
log.debug("[Startup]: Using Youtube_DL Version " + youtube_version)
log.debug("")

log.debug("[Startup]: Starting Up!")

client.run(os.environ.get("BOT_TOKEN", ""))
