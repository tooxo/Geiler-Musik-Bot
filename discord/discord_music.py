from discord.ext import commands
import discord
import random
import asyncio
from youtube_youtubedl import *
from spotify import *

class DiscordBot(commands.Cog):
    def __init__(self, bot):
        print("[Startup]: Initializing Music Module . . .")
        self.dictionary = {}
        self.bot = bot
        bot.remove_command("help")

    async def clear_presence(self,ctx):
        await self.dictionary[ctx.guild.id]['now_playing_message'].delete()
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))

    async def emptyChannel(self,ctx):
         if len(self.dictionary[ctx.guild.id]['voice_channel'].members) == 1:
             await self.dictionary[ctx.guild.id]['voice_client'].disconnect()
             embed=discord.Embed(title="I've left the channel, because it was empty.", color=0x00ffcc, url="https://f.chulte.de")
             await ctx.send(embed=embed)

    async def preloadNext(self,ctx):
        song_queue = self.dictionary[ctx.guild.id]['song_queue']
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

    def after_song(self, ctx):
        fur = asyncio.run_coroutine_threadsafe(self.clear_presence(ctx), self.bot.loop)
        try:
            fur.result()
        except Exception as e:
            print(e)
        l = asyncio.run_coroutine_threadsafe(self.emptyChannel(ctx), self.bot.loop)
        try:
            l.result()
        except Exception as e:
            print(e)
        fut = asyncio.run_coroutine_threadsafe(self.nextSong(ctx), self.bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(e)


    async def nextSong(self, ctx, type="next", url=None):
        dictionary = self.dictionary
        if (not dictionary[ctx.guild.id]['voice_client'].is_playing()) and len(dictionary[ctx.guild.id]['song_queue']) > 0:
            embed=discord.Embed(title="🔁 Loading ... 🔁", color=0x00ffcc, url="https://f.chulte.de")
            dictionary[ctx.guild.id]['now_playing_message'] = await ctx.send(embed=embed)
            try:
                a = dictionary[ctx.guild.id]['song_queue'][0]['title']
                a = dictionary[ctx.guild.id]['song_queue'][0]['link']
                a = dictionary[ctx.guild.id]['song_queue'][0]['stream']
                smalldict = dictionary[ctx.guild.id]['song_queue'][0]
            except Exception:
                try:
                    a = dictionary[ctx.guild.id]['song_queue'][0]['title']
                    a = dictionary[ctx.guild.id]['song_queue'][0]['link']
                    smalldict = await get_youtube_by_url_async(dictionary[ctx.guild.id]['song_queue'][0]['link'])
                except Exception:
                    smalldict = await youtube_search_by_term_async(dictionary[ctx.guild.id]['song_queue'][0]['title'])
            try:
                smalldict['user'] = dictionary[ctx.guild.id]['song_queue'][0]['user']
            except Exception as e:
                print(e)
            del dictionary[ctx.guild.id]['song_queue'][0]
            dictionary[ctx.guild.id]['now_playing_song'] = smalldict
            try:
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(smalldict['stream'], executable="ffmpeg", before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), volume=dictionary[ctx.guild.id]['volume'])
                dictionary[ctx.guild.id]['voice_client'].play(source, after=lambda _: self.after_song(ctx))
            except Exception:
                await dictionary[ctx.guild.id]['now_playing_message'].delete()
                embed = discord.Embed(title="Error while loading... Trying once again...", url="https://f.chulte.de")
                await ctx.send(embed=embed)
                embed=discord.Embed(title="🔁 Loading ... 🔁", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed=embed)
                stream = await youtube_search_by_term_async(smalldict['title'])
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(stream, executable="ffmpeg", before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), volume=dictionary[ctx.guild.id]['volume'])
                dictionary[ctx.guild.id]['voice_client'].play(source, after=lambda _: self.after_song(ctx))
            await self.bot.change_presence(activity=discord.Game(name=smalldict['title'], type=1))
            embed=discord.Embed(title="🎶 Now Playing: " + smalldict['title'] + " 🎶", color=0x00ffcc, url="https://f.chulte.de")
            await dictionary[ctx.guild.id]['now_playing_message'].edit(embed=embed)
            push_to_most_mongo_thread(smalldict['title'])
        elif type == "yt_term" and url is not None:
            smalldict = {}
            smalldict['title'] = url
            smalldict['user'] = ctx.message.author
            dictionary[ctx.guild.id]['song_queue'].append(smalldict)
            if not dictionary[ctx.guild.id]['voice_client'].is_playing():
                await self.nextSong(ctx)
            else:
                await ctx.send(':white_check_mark: Added one Song to Queue. :white_check_mark: ["'+ url + '"]')
        elif type == "yt_playlist" and url is not None:
            sick = await youtube_playlist_async(url)
            length = len(sick)
            for track in sick:
                track['user'] = ctx.message.author
                dictionary[ctx.guild.id]['song_queue'].append(track)
            embed = discord.Embed(title=":asterisk: Added " + str(length) + " Tracks to Queue. :asterisk:", url="https://f.chulte.de")
            await ctx.send(embed=embed)
            await self.nextSong(ctx)
        elif type == "sp_play" and url is not None:
            tracks = await playlist_fetch_spotify(url)
            length = len(tracks)
            for track in tracks:
                smalldict = dict()
                smalldict['title'] = track
                smalldict['user'] = ctx.message.author
                dictionary[ctx.guild.id]['song_queue'].append(smalldict)
            embed = discord.Embed(title=":asterisk: Added " + str(length) + " Tracks to Queue. :asterisk:", url="https://f.chulte.de")
            await ctx.send(embed=embed)
            await self.nextSong(ctx)
        elif type == "sp_track" and url is not None:
            track = await track_fetch_spotify(url)
            dictw = dict()
            dictw['title'] = track
            dictw['user'] = ctx.message.author
            dictionary[ctx.guild.id]['song_queue'].append(dictw)
            await self.nextSong(ctx)
        elif type == "yt_link" and url is not None:
            dic = await get_youtube_by_url_async(url)
            dic['user'] = ctx.message.author
            dictionary[ctx.guild.id]['song_queue'].append(dic)
            await self.nextSong(ctx)
        await self.preloadNext(ctx)

    @commands.command()
    async def ping(self, ctx):
        latency = self.bot.latency
        await ctx.send("My Ping is: " + str(latency))

    @commands.command()
    async def echo(self, ctx, *, content:str):
        await ctx.send(content)


    @commands.command()
    async def play(self, ctx, *, url:str):
        dictionary = self.dictionary
        try:
            dictionary[ctx.guild.id]['voice_channel'] = ctx.author.voice.channel
        except Exception as e:
            await ctx.send("You need to be in a channel.")
            return
        if dictionary[ctx.guild.id]['voice_client'] == None:
            dictionary[ctx.guild.id]['voice_client'] = await ctx.author.voice.channel.connect(timeout=60, reconnect=True)
        if 'youtube' in url:
            if "/watch?v=" in url:
                await self.nextSong(ctx, "yt_link", url)
            elif "playlist" in url:
                await self.nextSong(ctx, "yt_playlist", url)
        elif "spotify" in url:
            if "playlist" in url:
                await self.nextSong(ctx, "sp_play", url)
            elif "track" in url:
                await self.nextSong(ctx, "sp_track", url)
            else:
                await ctx.send("This type of link is unsupported.")
        else:
            await self.nextSong(ctx, "yt_term", url)


    async def cog_before_invoke(self, ctx):
        if ctx.guild.id not in self.dictionary:
            self.dictionary[ctx.guild.id] = dict()
        try:
            f = self.dictionary[ctx.guild.id]['song_queue']
        except:
            self.dictionary[ctx.guild.id]['song_queue'] = []
        try:
            f = self.dictionary[ctx.guild.id]['voice_client']
        except:
            self.dictionary[ctx.guild.id]['voice_client'] = None
        try:
            f = self.dictionary[ctx.guild.id]['voice_channel']
        except:
            self.dictionary[ctx.guild.id]['voice_channel'] = None
        try:
            f = self.dictionary[ctx.guild.id]['now_playing_ctx']
        except:
            self.dictionary[ctx.guild.id]['now_playing_ctx'] = None
        try:
            f = self.dictionary[ctx.guild.id]['now_playing_song']
        except:
            self.dictionary[ctx.guild.id]['now_playing_song'] = None
        try:
            f = self.dictionary[ctx.guild.id]['volume']
        except:
            self.dictionary[ctx.guild.id]['volume'] = 0.5

    @commands.command()
    async def queue(self, ctx):
        dictionary = self.dictionary
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

    @commands.command()
    async def rename(self, ctx, *, name:str):
        try:
            if len(name) > 32:
                embed=discord.Embed(title="Name too long. 32 chars is the limit.", url="https://f.chulte.de")
                await ctx.send(embed=embed)
            me = ctx.guild.me
            await me.edit(nick=name)
        except Exception as e:
            embed = discord.Embed(title="An Error occured: " + e, url="https://f.chulte.de")
            await ctx.send(embed=embed)

    @commands.command()
    async def volume(self, ctx, volume=329842372.3):
        dictionary = self.dictionary
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

    @commands.command()
    async def info(self, ctx):
        dictionary = self.dictionary
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

    @commands.command(aliases=["exit"])
    async def quit(self, ctx):
        try:
            await self.dictionary[ctx.guild.id]['voice_client'].disconnect()
            self.dictionary[ctx.guild.id]['voice_client'] = None
            self.dictionary[ctx.guild.id]['song-queue'] = []
            await self.clear_presence(ctx)
        except:
            pass

    @commands.command(aliases=["empty"])
    async def clear(self, ctx):
        if len(self.dictionary[ctx.guild.id]['song_queue']) is not 0:
            self.dictionary[ctx.guild.id]['song_queue'] = []
            embed = discord.Embed(title="Cleared the Queue. :cloud:", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="The Playlist was already empty! :cloud:", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)

    @commands.command(aliases=["mixer"])
    async def shuffle(self, ctx):
        if len(self.dictionary[ctx.guild.id]['song_queue']) > 0:
            random.shuffle(self.dictionary[ctx.guild.id]['song_queue'])
            embed = discord.Embed(title="Shuffled! :twisted_rightwards_arrows:", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)
            await self.preloadNext(ctx)

    @commands.command(aliases=["yeehee"])
    async def stop(self, ctx):
        dictionary = self.dictionary
        if dictionary[ctx.guild.id]['voice_client'] is not None:
            dictionary[ctx.guild.id]['song_queue'] = []
            dictionary[ctx.guild.id]['now_playing_song'] = None
            dictionary[ctx.guild.id]['voice_client'].stop()
            link = get_youtube_by_url("https://www.youtube.com/watch?v=siLkbdVxntU")
            source = discord.FFmpegPCMAudio(link['stream'], executable="ffmpeg", before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
            dictionary[ctx.guild.id]['voice_client'].play(source)
            embed=discord.Embed(title="Music Stopped! 🛑", color=0x00ffcc, url="https://f.chulte.de")
            if dictionary[ctx.guild.id]['voice_client'] is not None and dictionary[ctx.guild.id]['voice_client'].is_playing():
                await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title=":thinking: The Bot isn't connected. :thinking:", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)


    @commands.command(aliases=["halteein"])
    async def pause(self, ctx):
        dictionary = self.dictionary
        if dictionary[ctx.guild.id]['voice_client'] is not None:
            try:
                dictionary[ctx.guild.id]['voice_client'].pause()
                embed=discord.Embed(title="Paused! ⏸", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed=embed)
            except:
                embed=discord.Embed(title=":thinking: Nothing is playing... :thinking:", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed=embed)


    @commands.command(aliases=['next', 'müll'])
    async def skip(self, ctx):
        dictionary = self.dictionary
        embed=discord.Embed(title="Skipped! ⏭", color=0x00ffcc, url="https://f.chulte.de")
        nice = await ctx.send(embed=embed)
        dictionary[ctx.guild.id]['voice_client'].stop()
        await asyncio.sleep(5)
        await nice.delete()

    @commands.command(aliases=["unpause"])
    async def resume(self, ctx):
        dictionary = self.dictionary
        if dictionary[ctx.guild.id]['voice_client'] is not None:
            try:
                dictionary[ctx.guild.id]['voice_client'].resume()
                embed=discord.Embed(title="Unpaused! ⏯", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(title=":thinking: Nothing is running... :thinking:", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(DiscordBot(bot))
