from discord.ext import commands
import os
import discord

client = commands.Bot(command_prefix=".")
client.load_extension("discord_music")
client.load_extension("discord_text")

@client.event
async def on_ready():
    print("[Startup]: Finished.")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))

client.run(os.environ['BOT_TOKEN'])
