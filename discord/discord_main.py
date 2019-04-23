from discord.ext import commands
import os
import discord
from threading import Thread
import subprocess

client = commands.Bot(command_prefix=".")
client.load_extension("discord_music")
client.load_extension("discord_text")


def server():
    subprocess.call(['gunicorn', '--bind', '0.0.0.0:' + os.environ['PORT'], '--chdir', './stats', 'stats.wsgi:application'])

@client.event
async def on_ready():
    print("[Startup]: Finished.")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))
    t = Thread(target=server)
    t.start()

client.run(os.environ['BOT_TOKEN'])
