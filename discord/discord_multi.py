from discord.ext import commands
import discord
import random
import asyncio
import youtube_dl
import time
from youtube_youtubedl import *
from spotify import *
from statsWebServer import *

dictionary = dict()
prefix = "."
bot = commands.Bot(command_prefix=prefix)
bot.remove_command('help')
print("[STARTUP] Starting...")

@bot.event
async def on_ready():
    server_thread()
    print("[STARTUP] Finished.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))

async def clear_presence(context):
    global dictionary
    await dictionary[context.guild.id]['now_playing_message'].delete()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))

async def emptyChannel(context):
    global dictionary
    if len(dictionary[context.guild.id]['voice_channel'].members) == 1:
        await dictionary[context.guild.id]['voice_client'].disconnect()
        embed=discord.Embed(title="I've left the channel, because it was empty.", color=0x00ffcc, url="https://f.chulte.de")
        await context.send(embed=embed)

async def preloadNext(context):
    global dictionary
    song_queue = dictionary[context.guild.id]['song_queue']
    if len(song_queue) > 0:
        x = len(song_queue)
        for l in range(0, x):
            try:
                a = song_queue[l]['title']
                a = song_queue[l]['link']
                a = song_queue[l]['stream']
            except Exception:
                tempdict = await youtube_search_by_term_async(song_queue[l]['title'])
                tempdict['user'] = song_queue[l]['user']
                song_queue[l] = tempdict
                break

def after_geil(context):
    fur = asyncio.run_coroutine_threadsafe(clear_presence(context), bot.loop)
    try:
        fur.result()
    except Exception as e:
        print(e)
    l = asyncio.run_coroutine_threadsafe(emptyChannel(context), bot.loop)
    try:
        l.result()
    except Exception as e:
        print(e)
    fut = asyncio.run_coroutine_threadsafe(nextSong(context), bot.loop)
    try:
        fut.result()
    except Exception as e:
        print(e)

async def nextSong(context, type="next", url=None):
    global dictionary
    if (not dictionary[context.guild.id]['voice_client'].is_playing()) and len(dictionary[context.guild.id]['song_queue']) > 0:
        embed=discord.Embed(title="🔁 Loading ... 🔁", color=0x00ffcc, url="https://f.chulte.de")
        dictionary[context.guild.id]['now_playing_message'] = await context.send(embed=embed)
        try:
            a = dictionary[context.guild.id]['song_queue'][0]['title']
            a = dictionary[context.guild.id]['song_queue'][0]['link']
            a = dictionary[context.guild.id]['song_queue'][0]['stream']
            smalldict = dictionary[context.guild.id]['song_queue'][0]
        except Exception:
            try:
                a = dictionary[context.guild.id]['song_queue'][0]['title']
                a = dictionary[context.guild.id]['song_queue'][0]['link']
                smalldict = await get_youtube_by_url_async(dictionary[context.guild.id]['song_queue'][0]['link'])
            except Exception:
                smalldict = await youtube_search_by_term_async(dictionary[context.guild.id]['song_queue'][0]['title'])
        try:
            smalldict['user'] = dictionary[context.guild.id]['song_queue'][0]['user']
        except Exception as e:
            print(e)
        del dictionary[context.guild.id]['song_queue'][0]
        dictionary[context.guild.id]['now_playing_song'] = smalldict
        try:
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(smalldict['stream'], executable="ffmpeg", before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), volume=dictionary[context.guild.id]['volume'])
            dictionary[context.guild.id]['voice_client'].play(source, after=lambda _: after_geil(context))
        except Exception:
            await dictionary[context.guild.id]['now_playing_message'].delete()
            embed = discord.Embed(title="Error while loading... Trying once again...", url="https://f.chulte.de")
            await context.send(embed=embed)
            embed=discord.Embed(title="🔁 Loading ... 🔁", color=0x00ffcc, url="https://f.chulte.de")
            await context.send(embed=embed)
            stream = await youtube_search_by_term_async(smalldict['title'])
            source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(stream, executable="ffmpeg", before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), volume=dictionary[context.guild.id]['volume'])
            dictionary[context.guild.id]['voice_client'].play(source, after=lambda _: after_geil(context))
        await bot.change_presence(activity=discord.Game(name=smalldict['title'], type=1))
        embed=discord.Embed(title="🎶 Now Playing: " + smalldict['title'] + " 🎶", color=0x00ffcc, url="https://f.chulte.de")
        await dictionary[context.guild.id]['now_playing_message'].edit(embed=embed)
        push_to_most_mongo_thread(smalldict['title'])
    elif type == "yt_term" and url is not None:
        smalldict = {}
        smalldict['title'] = url
        smalldict['user'] = context.message.author
        dictionary[context.guild.id]['song_queue'].append(smalldict)
        if not dictionary[context.guild.id]['voice_client'].is_playing():
            await nextSong(context)
        else:
            await context.send(':white_check_mark: Added one Song to Queue. :white_check_mark: ["'+ url + '"]')
    elif type == "yt_playlist" and url is not None:
        sick = await youtube_playlist_async(url)
        length = len(sick)
        for track in sick:
            track['user'] = context.message.author
            dictionary[context.guild.id]['song_queue'].append(track)
        embed = discord.Embed(title=":asterisk: Added " + str(length) + " Tracks to Queue. :asterisk:", url="https://f.chulte.de")
        await context.send(embed=embed)
        await nextSong(context)
    elif type == "sp_play" and url is not None:
        tracks = await playlist_fetch_spotify(url)
        length = len(tracks)
        for track in tracks:
            smalldict = dict()
            smalldict['title'] = track
            smalldict['user'] = context.message.author
            dictionary[context.guild.id]['song_queue'].append(smalldict)
        embed = discord.Embed(title=":asterisk: Added " + str(length) + " Tracks to Queue. :asterisk:", url="https://f.chulte.de")
        await context.send(embed=embed)
        await nextSong(context)
    elif type == "sp_track" and url is not None:
        track = await track_fetch_spotify(url)
        dictw = dict()
        dictw['title'] = track
        dictw['user'] = context.message.author
        dictionary[context.guild.id]['song_queue'].append(dictw)
        await nextSong(context)
    elif type == "yt_link" and url is not None:
        dic = await get_youtube_by_url_async(url)
        dic['user'] = context.message.author
        dictionary[context.guild.id]['song_queue'].append(dic)
        await nextSong(context)
    await preloadNext(context)

@bot.command(pass_context=True)
async def ping(ctx):
    latency = bot.latency
    await ctx.send("My Ping is: " + str(latency))

@bot.command(pass_context=True)
async def echo(ctx, *, content:str):
    await ctx.send(content)

@bot.command(pass_context=True, aliases=["clemi", "god", "gott"])
async def cool(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/357956193093812234/563063266457288714/Unbenanntw2.jpg")

@bot.command(pass_context=True)
async def dani(ctx):
    await ctx.send("https://tenor.com/view/suffer-time-gif-7212239")

@bot.command(pass_context=True)
async def play(ctx, *, url:str):
    global dictionary
    try:
        dictionary[ctx.guild.id]['voice_channel'] = ctx.author.voice.channel
    except Exception as e:
        await ctx.send("You need to be in a channel.")
        return
    if dictionary[ctx.guild.id]['voice_client'] == None:
        dictionary[ctx.guild.id]['voice_client'] = await ctx.author.voice.channel.connect(timeout=60, reconnect=True)
    if 'youtube' in url:
        if "/watch?v=" in url:
            await nextSong(ctx, "yt_link", url)
        elif "playlist" in url:
            await nextSong(ctx, "yt_playlist", url)
    elif "spotify" in url:
        if "playlist" in url:
            await nextSong(ctx, "sp_play", url)
        elif "track" in url:
            await nextSong(ctx, "sp_track", url)
        else:
            await ctx.send("This type of link is unsupported.")
    else:
        await nextSong(ctx, "yt_term", url)

@bot.command(pass_context=True)
async def queue(ctx):
    global dictionary
    song_queue = dictionary[ctx.guild.id]['song_queue']
    np_song = dictionary[ctx.guild.id]['now_playing_song']
    embed=discord.Embed(color=0x00ffcc, url="https://f.chulte.de")
    try:
        embed.add_field(name="Currently Playing...", value=np_song['title'] + "\n", inline=False)
    except:
        embed.add_field(name="Currently Playing...", value="Nothing.\n", inline=False)
    if len(song_queue) > 0:
        numbers = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:"]
        title = "🎶 COMING UP: 🎶\n"
        queue = ""
        for x in range(0, 9):
            try:
                queue = queue + numbers[x] + " " + song_queue[x]['title'] + "\n"
            except:
                pass
        if (len(song_queue) - 9) > 0:
            queue = queue + ":hash: " + str(len(song_queue) - 9) + " Tracks..."
        embed.add_field(name="🎶 COMING UP: 🎶", value=queue, inline=False)
    else:
        embed.add_field(name="🎶 COMING UP: 🎶", value="🚫 Nothing in Queue. Use .play to add something. 🚫", inline=False)

    await ctx.send(embed=embed)

@bot.command(pass_context=True)
async def rename(ctx, *, name:str):
    try:
        if len(name) > 32:
            embed=discord.Embed(title="Name too long. 32 chars is the limit.", url="https://f.chulte.de")
            ctx.send(embed=embed)
        me = ctx.guild.me
        await me.edit(nick=name)
    except Exception as e:
        embed = discord.Embed(title="An Error occured: " + e, url="https://f.chulte.de")
        await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    global dictionary
    if message.guild.id not in dictionary:
        dictionary[message.guild.id] = dict()
    try:
        f = dictionary[message.guild.id]['song_queue']
    except:
        dictionary[message.guild.id]['song_queue'] = []
    try:
        f = dictionary[message.guild.id]['voice_client']
    except:
        dictionary[message.guild.id]['voice_client'] = None
    try:
        f = dictionary[message.guild.id]['voice_channel']
    except:
        dictionary[message.guild.id]['voice_channel'] = None
    try:
        f = dictionary[message.guild.id]['now_playing_message']
    except:
        dictionary[message.guild.id]['now_playing_message'] = None
    try:
        f = dictionary[message.guild.id]['now_playing_song']
    except:
        dictionary[message.guild.id]['now_playing_song'] = None
    try:
        f = dictionary[message.guild.id]['volume']
    except:
        dictionary[message.guild.id]['volume'] = 0.5

    await bot.process_commands(message)

@bot.command(pass_context=True)
async def volume(ctx, volume=329842372.3):
    global dictionary
    if volume == 329842372.3:
        embed=discord.Embed(title="The current volume is: " + str(dictionary[ctx.guild.id]['volume']) + ". It only updates on song changes, so beware.", color=0x00ffcc, url="https://f.chulte.de")
        await ctx.send(embed=embed)
        return
    try:
        var = float(volume)
    except Exception as e:
        embed=discord.Embed(title="You need to enter a number.", color=0x00ffcc, url="https://f.chulte.de")
        await ctx.send(embed=embed)
        return
    if var < 0 or var > 2:
        embed=discord.Embed(title="The number needs to be between 0.0 and 2.0.", color=0x00ffcc, url="https://f.chulte.de")
        await ctx.send(embed=embed)
        return
    dictionary[ctx.guild.id]['volume'] = var
    embed=discord.Embed(title="The Volume was set to: " + str(var), color=0x00ffcc, url="https://f.chulte.de")
    await ctx.send(embed=embed)

@bot.command(pass_context=True, aliases=["mixer"])
async def shuffle(ctx):
    global dictionary
    if len(dictionary[ctx.guild.id]['song_queue']) > 0:
        random.shuffle(dictionary[ctx.guild.id]['song_queue'])
        embed = discord.Embed(title="Shuffled! :twisted_rightwards_arrows:", color=0x00ffcc, url="https://f.chulte.de")
        await ctx.send(embed=embed)
        await preloadNext(ctx)

@bot.command(pass_context=True)
async def niki(ctx):
    await ctx.send("https://cdn.discordapp.com/attachments/561858486430859266/563436218914701322/Niki_Nasa.png")

@bot.command(pass_context=True)
async def info(ctx):
    global dictionary
    if dictionary[ctx.guild.id]['now_playing_song'] is None:
        embed = discord.Embed(title="Information", description="Nothing is playing right now.", color=0x00ffcc, url="https://f.chulte.de")
        await ctx.send(embed=embed)
        return
    try:
        embed = discord.Embed(title="Information", description="Name: " + dictionary[ctx.guild.id]['now_playing_song']['title'] + "\nStreamed from: " + dictionary[ctx.guild.id]['now_playing_song']['link'] + "\nDuration: " + dictionary[ctx.guild.id]['now_playing_song']['duration'] + "\nRequested by: <@!" + str(dictionary[ctx.guild.id]['now_playing_song']['user'].id) + ">\nLoaded in: " + str(round(dictionary[ctx.guild.id]['now_playing_song']['loadtime'], 2)) + " sec.", color=0x00ffcc, url="https://f.chulte.de")
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)
        embed = discord.Embed(title="Error", description="An error occured, while checking info.", url="https://f.chulte.de")
        await ctx.send(embed=embed)

@bot.command(pass_context=True, aliases=["exit"])
async def quit(ctx):
    try:
        global dictionary
        await dictionary[ctx.guild.id]['voice_client'].disconnect()
        dictionary[ctx.guild.id]['voice_client'] = None
        dictionary[ctx.guild.id]['song-queue'] = []
        await clear_presence(ctx)
    except:
        pass

@bot.command(pass_context=True, aliases=["yeehee", "clear"])
async def stop(ctx):
    global dictionary
    if dictionary[ctx.guild.id]['voice_client'] is not None:
        dictionary[ctx.guild.id]['song_queue'] = []
        dictionary[ctx.guild.id]['now_playing_song'] = None
        dictionary[ctx.guild.id]['voice_client'].stop()
        link = get_youtube_by_url("https://www.youtube.com/watch?v=siLkbdVxntU")
        source = discord.FFmpegPCMAudio(link['stream'], executable="ffmpeg", before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
        dictionary[ctx.guild.id]['voice_client'].play(source)
        embed=discord.Embed(title="Music Stopped! 🛑", color=0x00ffcc, url="https://f.chulte.de")
        await ctx.send(embed=embed)
    else:
        embed=discord.Embed(title=":thinking: The Bot isn't connected. :thinking:", color=0x00ffcc, url="https://f.chulte.de")
        await ctx.send(embed=embed)

@bot.command(pass_context=True, aliases=["halteein"])
async def pause(ctx):
    global dictionary
    if dictionary[ctx.guild.id]['voice_client'] is not None:
        try:
            dictionary[ctx.guild.id]['voice_client'].pause()
            embed=discord.Embed(title="Paused! ⏸", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)
        except:
            embed=discord.Embed(title=":thinking: Nothing is playing... :thinking:", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)

@bot.command(pass_context=True, aliases=['next', 'müll'])
async def skip(ctx):
    global dictionary
    embed=discord.Embed(title="Skipped! ⏭", color=0x00ffcc, url="https://f.chulte.de")
    nice = await ctx.send(embed=embed)
    dictionary[ctx.guild.id]['voice_client'].stop()
    await asyncio.sleep(5)
    await nice.delete()

@bot.command(pass_context=True)
async def help(ctx):
    embed=discord.Embed(title="Help", color=0x00ffcc, url="https://f.chulte.de")
    embed.add_field(name="Music Commands", value=".play [songname/link] - Plays a song, Spotify and YouTube are supported. \n.stop - Stops the Playback \n.pause - Pauses the Music \n.resume - Resumes the music \n.shuffle - Shuffles the Queue \n.queue - Shows the coming up songs. \n.volume <num between 0.0 and 2.0> - Changes the playback volume, only updates on song changes.", inline=False)
#    embed.add_field(name="lolz commands", value=".clemi \n.dani \n.niki", inline=False)
    embed.add_field(name="Debug Commands", value=".np - More infos about the currently playing song\n.ping - Shows the bot's ping \n.echo - [text] - Echoes the text back.\n.rename [name] - Renames the Bot", inline=False)
    embed.set_footer(text="despacito")
    await ctx.send(embed=embed)

@bot.command(pass_context=True, aliases=["unpause"])
async def resume(ctx):
    global dictionary
    if dictionary[ctx.guild.id]['voice_client'] is not None:
        try:
            dictionary[ctx.guild.id]['voice_client'].resume()
            embed=discord.Embed(title="Unpaused! ⏯", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(title=":thinking: Nothing is running... :thinking:", color=0x00ffcc, url="https://f.chulte.de")
            ctx.send(embed=embed)

token = os.environ['bot_token']
bot.run(token)
