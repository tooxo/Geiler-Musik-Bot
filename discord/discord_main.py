from discord.ext import commands
import os
import discord
import asyncio

if os.environ.get('TEST_ENVIRONMENT', 'False') == 'True':
    prefix = ','
else:
    prefix = '.'

client = commands.Bot(command_prefix=prefix)
client.load_extension("discord_music")
client.load_extension("discord_text")


@client.event
async def on_ready():
    print("[Startup]: Finished.")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))


@client.event
async def on_command_error(ctx, error):
    if 'not found' in str(error):
        embed = discord.Embed(title=str(error), color=0x00ffcc, url='https://github.com/tooxo/Geiler-Musik-Bot/issues')
        await ctx.send(embed=embed)
    else:
        print(error)


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
