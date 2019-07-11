from discord.ext import commands
import os
import discord
import asyncio
import sys

client = commands.Bot(command_prefix=".")
client.load_extension("discord_music")
client.load_extension("discord_text")


@client.event
async def on_ready():
    print("[Startup]: Finished.")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))


loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(client.start(os.environ['BOT_TOKEN']))
except KeyboardInterrupt:

    def yikes(f):
        loop.stop()


    future = asyncio.ensure_future(client.logout(), loop=loop)
    future.add_done_callback(yikes)
    loop.run_forever()
finally:
    client.loop.stop()
