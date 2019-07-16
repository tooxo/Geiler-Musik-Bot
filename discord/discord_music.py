from discord.ext import commands
import discord
import random
import asyncio
import spotify
import youtube
import mongo
import time


class DiscordBot(commands.Cog):
    def __init__(self, bot):
        print("[Startup]: Initializing Music Module . . .")
        self.dictionary = {}
        self.bot = bot
        self.spotify = spotify.Spotify()
        self.youtube = youtube.Youtube()
        self.mongo = mongo.Mongo()
        bot.remove_command("help")

        if not discord.opus.is_loaded():
            discord.opus.load_opus('/usr/lib/libopus.so')

    async def clear_presence(self, ctx):
        await self.dictionary[ctx.guild.id]['now_playing_message'].delete()
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=".help"))

    async def message_cycle(self, message, ctx, full, empty):
        await asyncio.sleep(1)
        try:
            if self.dictionary[ctx.guild.id]['now_playing_song']['is_paused'] is False:
                now_time = int(time.time()) - self.dictionary[ctx.guild.id]['now_playing_song']['start_time'] - \
                           self.dictionary[ctx.guild.id]['now_playing_song']['pause_duration']

                if ':' in str(self.dictionary[ctx.guild.id]['now_playing_song']['duration']):
                    finish_second = int(
                        str(self.dictionary[ctx.guild.id]['now_playing_song']['duration']).split(":")[
                            0]) * 3600 + int(
                        str(self.dictionary[ctx.guild.id]['now_playing_song']['duration']).split(":")[
                            1]) * 60 + int(
                        str(self.dictionary[ctx.guild.id]['now_playing_song']['duration']).split(":")[2])
                    description = time.strftime('%H:%M:%S', time.gmtime(now_time)) + " / " + \
                        str(self.dictionary[ctx.guild.id]['now_playing_song']['duration'])
                else:
                    finish_second = int(self.dictionary[ctx.guild.id]['now_playing_song']['duration'])
                    description = time.strftime('%H:%M:%S', time.gmtime(now_time)) + " / " + \
                        time.strftime('%H:%M:%S', time.gmtime(
                                      self.dictionary[ctx.guild.id]['now_playing_song']['duration']))

                percentage = int((now_time / finish_second) * 100)

                if percentage > 100:
                    percentage = 100
                count = percentage / 4
                hashes = ""
                while count > 0:
                    hashes += full
                    count -= 1
                while len(hashes) < 25:
                    hashes += empty
                hashes += " " + str(percentage) + "%"
                embed2 = discord.Embed(title=self.dictionary[ctx.guild.id]['now_playing_song']['title'],
                                       color=0x00ffcc, url=self.dictionary[ctx.guild.id]['now_playing_song']['link'])
                embed2.set_author(name="Currently Playing:")
                embed2.add_field(name=hashes, value=description)
                try:
                    await message.edit(embed=embed2)
                except discord.NotFound:
                    return
                if now_time >= finish_second:
                    return
        except TypeError:
            return
        await self.message_cycle(message, ctx, full, empty)

    async def empty_channel(self, ctx):
        if len(self.dictionary[ctx.guild.id]['voice_channel'].members) == 1:
            self.dictionary[ctx.guild.id]['song_queue'] = []
            await self.dictionary[ctx.guild.id]['voice_client'].disconnect()
            embed = discord.Embed(title="I've left the channel, because it was empty.", color=0x00ffcc,
                                  url="https://f.chulte.de")
            await ctx.send(embed=embed)

    async def preload_next(self, ctx):
        song_queue = self.dictionary[ctx.guild.id]['song_queue']
        if len(song_queue) > 0:
            x = len(song_queue)
            for l in range(0, x):
                if 'title' not in song_queue[l] or 'link' not in song_queue[l] or 'stream' not in song_queue[l]:
                    temp_dict = await self.youtube.youtube_term(song_queue[l]['title'])
                    temp_dict['user'] = song_queue[l]['user']
                    song_queue[l] = temp_dict
                    break
                else:
                    continue

    def after_song(self, ctx):
        function = asyncio.run_coroutine_threadsafe(self.clear_presence(ctx), self.bot.loop)
        try:
            function.result()
        except Exception as e:
            print(e)
        function = asyncio.run_coroutine_threadsafe(self.empty_channel(ctx), self.bot.loop)
        try:
            function.result()
        except Exception as e:
            print(e)
        function = asyncio.run_coroutine_threadsafe(self.next_song(ctx), self.bot.loop)
        try:
            function.result()
        except Exception as e:
            print(e)

    async def next_song(self, ctx, function="next", url=None):
        dictionary = self.dictionary
        if dictionary[ctx.guild.id]['voice_client'] is None:
            return
        if (not dictionary[ctx.guild.id]['voice_client'].is_playing()) and len(
                dictionary[ctx.guild.id]['song_queue']) > 0:
            embed = discord.Embed(title="🔁 Loading ... 🔁", color=0x00ffcc, url="https://f.chulte.de")
            dictionary[ctx.guild.id]['now_playing_message'] = await ctx.send(embed=embed)
            if 'title' in dictionary[ctx.guild.id]['song_queue'][0] \
                    and 'link' in dictionary[ctx.guild.id]['song_queue'][0] \
                    and 'stream' in dictionary[ctx.guild.id]['song_queue'][0]:
                small_dict = dictionary[ctx.guild.id]['song_queue'][0]
            elif 'title' in dictionary[ctx.guild.id]['song_queue'][0] \
                    and 'link' in dictionary[ctx.guild.id]['song_queue'][0]:
                small_dict = await self.youtube.youtube_url(dictionary[ctx.guild.id]['song_queue'][0]['link'])
            else:
                small_dict = await self.youtube.youtube_term(dictionary[ctx.guild.id]['song_queue'][0]['title'])
            # try:
            #     a = dictionary[ctx.guild.id]['song_queue'][0]['title']
            #     a = dictionary[ctx.guild.id]['song_queue'][0]['link']
            #     a = dictionary[ctx.guild.id]['song_queue'][0]['stream']
            #     small_dict = dictionary[ctx.guild.id]['song_queue'][0]
            # except KeyError:
            #     try:
            #         o = dictionary[ctx.guild.id]['song_queue'][0]['title']
            #         o = dictionary[ctx.guild.id]['song_queue'][0]['link']
            #         small_dict = await self.youtube.youtubeUrl(dictionary[ctx.guild.id]['song_queue'][0]['link'])
            #     except KeyError:
            #         small_dict = await self.youtube.youtubeTerm(dictionary[ctx.guild.id]['song_queue'][0]['title'])
            if small_dict['error'] is True:
                embed = discord.Embed(title="Error while loading.", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed)
                self.after_song(ctx)
            try:
                small_dict['user'] = dictionary[ctx.guild.id]['song_queue'][0]['user']
            except Exception as e:
                print(e)
            del dictionary[ctx.guild.id]['song_queue'][0]
            dictionary[ctx.guild.id]['now_playing_song'] = small_dict
            volume = await self.mongo.get_volume(ctx.guild.id)
            try:
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(small_dict['stream'],
                                           executable="ffmpeg",

                                           before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
                    volume=volume)
                dictionary[ctx.guild.id]['voice_client'].play(source, after=lambda _: self.after_song(ctx))
            except Exception as e:
                print('song_loading_error', e)
                await dictionary[ctx.guild.id]['now_playing_message'].delete()
                embed = discord.Embed(title="Error while loading... Trying once again...", url="https://f.chulte.de",
                                      color=0x00ffcc)
                await ctx.send(embed=embed)
                embed = discord.Embed(title="🔁 Loading ... 🔁", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed=embed)
                stream = await self.youtube.youtube_term(small_dict['title'])
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(stream,
                                           executable="ffmpeg",
                                           before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"),
                    volume=volume)
                dictionary[ctx.guild.id]['voice_client'].play(source, after=lambda _: self.after_song(ctx))
            await self.bot.change_presence(activity=discord.Game(name=small_dict['title'], type=1))
            dictionary[ctx.guild.id]['now_playing_song']['start_time'] = int(time.time())
            dictionary[ctx.guild.id]['now_playing_song']['is_paused'] = False
            dictionary[ctx.guild.id]['now_playing_song']['pause_duration'] = 0

            hash_full, hash_empty = await self.mongo.get_chars(ctx.guild.id)

            now_position = int(time.time()) - self.dictionary[ctx.guild.id]['now_playing_song']['start_time'] - \
                self.dictionary[ctx.guild.id]['now_playing_song']['pause_duration']

            if ':' in str(self.dictionary[ctx.guild.id]['now_playing_song']['duration']):
                end_position = int(
                    str(self.dictionary[ctx.guild.id]['now_playing_song']['duration']).split(":")[
                        0]) * 3600 + int(
                    str(self.dictionary[ctx.guild.id]['now_playing_song']['duration']).split(":")[
                        1]) * 60 + int(
                    str(self.dictionary[ctx.guild.id]['now_playing_song']['duration']).split(":")[2])
                description = time.strftime('%H:%M:%S', time.gmtime(now_position)) + " / " + \
                    str(self.dictionary[ctx.guild.id]['now_playing_song']['duration'])
            else:
                end_position = int(self.dictionary[ctx.guild.id]['now_playing_song']['duration'])
                description = time.strftime('%H:%M:%S', time.gmtime(now_position)) + " / " + \
                    time.strftime('%H:%M:%S',
                                  time.gmtime(
                                      self.dictionary[ctx.guild.id]['now_playing_song']['duration'])
                                  )
            percentage = int((now_position / end_position) * 100)
            count = int(percentage / 4)
            hashes = ''
            while count > 0:
                hashes += hash_full
                count -= 1

            while len(hashes) < 25:
                hashes += hash_empty

            embed = discord.Embed(title=self.dictionary[ctx.guild.id]['now_playing_song']['title'], color=0x00ffcc,
                                  url=self.dictionary[ctx.guild.id]['now_playing_song']['link'])
            embed.set_author(name='Currently Playing:')
            embed.add_field(name=hashes, value=description)
            await dictionary[ctx.guild.id]['now_playing_message'].edit(embed=embed)
            await self.mongo.append_most_played(small_dict['title'])
            await self.message_cycle(dictionary[ctx.guild.id]['now_playing_message'], ctx, hash_full, hash_empty)
            await ctx.message.delete()

        elif function == "yt_term" and url is not None:
            small_dict = dict()
            small_dict['title'] = url
            small_dict['user'] = ctx.message.author
            dictionary[ctx.guild.id]['song_queue'].append(small_dict)
            if not dictionary[ctx.guild.id]['voice_client'].is_playing():
                await self.next_song(ctx)
            else:
                embed = discord.Embed(
                    title=':asterisk: Added **' + url + '** to Queue.',
                    url="https://f.chulte.de", color=0x00ffcc)
                await ctx.send(embed=embed)
        elif function == "yt_playlist" and url is not None:
            sick = await self.youtube.youtube_playlist(url)
            length = len(sick)
            for track in sick:
                track['user'] = ctx.message.author
                dictionary[ctx.guild.id]['song_queue'].append(track)
            embed = discord.Embed(title=":asterisk: Added " + str(length) + " Tracks to Queue. :asterisk:",
                                  url="https://f.chulte.de", color=0x00ffcc)
            await ctx.send(embed=embed)
            await self.next_song(ctx)
        elif function == "sp_play" and url is not None:
            tracks = await self.spotify.spotify_playlist(url)
            length = len(tracks)
            if length == 0:
                embed = discord.Embed(title="**There was an error pulling the Spotify Playlist, 0 Songs were added.**",
                                      url="https://github.com/tooxo/Geiler-Musik-Bot/issues", color=0x00ffcc)
                await ctx.send(embed=embed)
                return
            for track in tracks:
                small_dict = dict()
                small_dict['title'] = track
                small_dict['user'] = ctx.message.author
                dictionary[ctx.guild.id]['song_queue'].append(small_dict)
            embed = discord.Embed(title=":asterisk: Added " + str(length) + " Tracks to Queue. :asterisk:",
                                  url="https://f.chulte.de", color=0x00ffcc)
            await ctx.send(embed=embed)
            await self.next_song(ctx)
        elif function == "sp_track" and url is not None:
            track = await self.spotify.spotify_track(url)
            dictw = dict()
            dictw['title'] = track
            dictw['user'] = ctx.message.author
            dictionary[ctx.guild.id]['song_queue'].append(dictw)
            if not self.dictionary[ctx.guild.id]['voice_client'].is_playing():
                await self.next_song(ctx)
            else:
                embed = discord.Embed(title=':asterisk: Added **' + track + '** to Queue.', url='https://f.chulte.de',
                                      color=0x00ffcc)
                await ctx.send(embed=embed)
        elif function == "sp_album" and url is not None:
            tracks = await self.spotify.spotify_album(url)
            for track in tracks:
                dic = dict()
                dic['title'] = track
                dic['user'] = ctx.message.author
                dictionary[ctx.guild.id]['song_queue'].append(dic)
            embed = discord.Embed(title=":asterisk: Added " + str(len(tracks)) + " Tracks to Queue. :asterisk:",
                                  url="https://f.chulte.de", color=0x00ffcc)
            await ctx.send(embed=embed)
            await self.next_song(ctx)
        elif function == "sp_artist" and url is not None:
            tracks = await self.spotify.spotify_artist(url)
            for track in tracks:
                dic = dict()
                dic['title'] = track
                dic['user'] = ctx.message.author
                dictionary[ctx.guild.id]['song_queue'].append(dic)
            embed = discord.Embed(title=":asterisk: Added " + str(len(tracks)) + " Tracks to Queue. :asterisk:",
                                  url="https://f.chulte.de", color=0x00ffcc)
            await ctx.send(embed=embed)
            await self.next_song(ctx)
        elif function == "yt_link" and url is not None:
            dic = await self.youtube.youtube_url(url)
            dic['user'] = ctx.message.author
            dictionary[ctx.guild.id]['song_queue'].append(dic)
            if not self.dictionary[ctx.guild.id]['voice_client'].is_playing():
                await self.next_song(ctx)
            else:
                embed = discord.Embed(title=':asterisk: Added **' + dic['title'] + '** to Queue.',
                                      url='https://f.chulte.de', color=0x00ffcc)
                await ctx.send(embed=embed)
        await self.preload_next(ctx)

    @commands.command()
    async def echo(self, ctx, *, content: str):
        await ctx.send(content)

    @commands.command(aliases=["p"])
    async def play(self, ctx, *, url: str):
        dictionary = self.dictionary
        try:
            dictionary[ctx.guild.id]['voice_channel'] = ctx.author.voice.channel
        except Exception as e:
            print('channel_join', e)
            embed = discord.Embed(title="You need to be in a channel.", color=0x00ffcc, url="https://f.chulte.de")
            dictionary[ctx.guild.id]['voice_channel'] = None
            await ctx.send(embed=embed)
            return
        if dictionary[ctx.guild.id]['voice_client'] is None:
            try:
                if ctx.author.voice.channel.user_limit <= len(
                        ctx.author.voice.channel.members) and ctx.author.voice.channel.user_limit != 0:
                    if ctx.guild.me.guild_permissions.administrator is True:
                        dictionary[ctx.guild.id]['voice_client'] = await ctx.author.voice.channel.connect(
                            timeout=60,
                            reconnect=True
                        )
                    else:
                        embed = discord.Embed(title="Error while joining your channel. :frowning: (1)",
                                              url="https://f.chulte.de",
                                              color=0x00ffcc)
                        await ctx.send(embed=embed)
                        return
                else:
                    dictionary[ctx.guild.id]['voice_client'] = await ctx.author.voice.channel.connect(timeout=60,
                                                                                                      reconnect=True)
            except TimeoutError and discord.HTTPException and discord.ClientException and discord.DiscordException as e:
                print('channel_join', e)
                dictionary[ctx.guild.id]['voice_channel'] = None
                embed = discord.Embed(title="Error while joining your channel. :frowning: (2)",
                                      url="https://f.chulte.de",
                                      color=0x00ffcc)
                await ctx.send(embed=embed)
        if 'youtube' in url:
            if "/watch?v=" in url:
                await self.next_song(ctx, "yt_link", url)
            elif "playlist" in url:
                await self.next_song(ctx, "yt_playlist", url)
        elif 'spotify' in url:
            if "playlist" in url:
                await self.next_song(ctx, "sp_play", url)
            elif "track" in url:
                await self.next_song(ctx, "sp_track", url)
            elif "album" in url:
                await self.next_song(ctx, "sp_album", url)
            elif "artist" in url:
                await self.next_song(ctx, "sp_artist", url)
            else:
                embed = discord.Embed(title="This type of link is unsupported.", color=0x00ffcc,
                                      url="https://f.chulte.de")
                await ctx.send(embed=embed)
        elif url == 'charts':
            charts_url = 'https://open.spotify.com/user/spotifycharts/' \
                         'playlist/37i9dQZEVXbMDoHDwVN2tF?si=TTsODvC1S8uXfXtKq2VrRg'
            await self.next_song(ctx,
                                 'sp_play',
                                 charts_url
                                 )
        else:
            await self.next_song(ctx, "yt_term", url)

    async def cog_before_invoke(self, ctx):
        if ctx.guild.id not in self.dictionary:
            self.dictionary[ctx.guild.id] = dict()
        if 'song_queue' not in self.dictionary[ctx.guild.id]:
            self.dictionary[ctx.guild.id]['song_queue'] = []
        if 'voice_client' not in self.dictionary[ctx.guild.id]:
            self.dictionary[ctx.guild.id]['voice_client'] = None
        if 'voice_channel' not in self.dictionary[ctx.guild.id]:
            self.dictionary[ctx.guild.id]['voice_channel'] = None
        if 'now_playing_song' not in self.dictionary[ctx.guild.id]:
            self.dictionary[ctx.guild.id]['now_playing_song'] = None

    @commands.command(aliases=['q'])
    async def queue(self, ctx):
        dictionary = self.dictionary
        song_queue = dictionary[ctx.guild.id]['song_queue']
        np_song = dictionary[ctx.guild.id]['now_playing_song']
        embed = discord.Embed(color=0x00ffcc, url="https://f.chulte.de")
        if np_song is not None:
            embed.add_field(name="**Currently Playing...**", value=np_song['title'] + "\n", inline=False)
        else:
            embed.add_field(name="**Currently Playing...**", value="Nothing.\n", inline=False)
        if len(song_queue) > 0:
            numbers = [":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:"]
            queue = ""
            for x in range(0, 9):
                if 'title' in song_queue[x]:
                    queue = queue + numbers[x] + " " + song_queue[x]['title'] + "\n"
                else:
                    break
            if (len(song_queue) - 9) > 0:
                queue = queue + ":hash: " + str(len(song_queue) - 9) + " Tracks..."
            embed.add_field(name="**Coming up:**", value=queue, inline=False)
        else:
            embed.add_field(name="**Coming up:**", value="Nothing in Queue. Use .play to add something.",
                            inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def rename(self, ctx, *, name: str):
        try:
            if len(name) > 32:
                embed = discord.Embed(title="Name too long. 32 chars is the limit.", url="https://f.chulte.de",
                                      color=0x00ffcc)
                await ctx.send(embed=embed)
            me = ctx.guild.me
            await me.edit(nick=name)
            embed = discord.Embed(title="Rename to **" + name + "** successful.", url='https://f.chulte.de',
                                  color=0x00ffcc)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="An Error occured: " + str(e), url="https://f.chulte.de", color=0x00ffcc)
            await ctx.send(embed=embed)

    @commands.command(aliases=['v'])
    async def volume(self, ctx, volume=None):
        current_volume = await self.mongo.get_volume(ctx.guild.id)
        if volume is None:
            embed = discord.Embed(
                title="The current volume is: " + str(current_volume) + ". It only updates on song changes, so beware.",
                color=0x00ffcc,
                url="https://f.chulte.de")
            await ctx.send(embed=embed)
            return
        try:
            var = float(volume)
        except ValueError as e:
            print('volume_value_error', e)
            embed = discord.Embed(title="You need to enter a number.", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)
            return
        if var < 0 or var > 2:
            embed = discord.Embed(title="The number needs to be between 0.0 and 2.0.", color=0x00ffcc,
                                  url="https://f.chulte.de")
            await ctx.send(embed=embed)
            return
        await self.mongo.set_volume(ctx.guild.id, var)
        embed = discord.Embed(title="The Volume was set to: " + str(var), color=0x00ffcc, url="https://f.chulte.de")
        await ctx.send(embed=embed)

    @commands.command()
    async def info(self, ctx):
        dictionary = self.dictionary
        if dictionary[ctx.guild.id]['now_playing_song'] is None:
            embed = discord.Embed(title="Information", description="Nothing is playing right now.", color=0x00ffcc,
                                  url="https://f.chulte.de")
            await ctx.send(embed=embed)
            return
        try:
            embed = discord.Embed(title="Information", description="Name: " + str(
                dictionary[ctx.guild.id]['now_playing_song']['title']) + "\nStreamed from: " + str(
                dictionary[ctx.guild.id]['now_playing_song']['link']) + "\nDuration: " + str(
                dictionary[ctx.guild.id]['now_playing_song']['duration']) + "\nRequested by: <@!" + str(
                dictionary[ctx.guild.id]['now_playing_song']['user'].id) + ">\nLoaded in: " + str(
                round(dictionary[ctx.guild.id]['now_playing_song']['loadtime'],
                      2)) + " sec." + "\nSearched Term: " + str(dictionary[ctx.guild.id]['now_playing_song']['term']),
                                  color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
            embed = discord.Embed(title="Error", description="An error occurred while checking info.",
                                  url="https://f.chulte.de", color=0x00ffcc)
            await ctx.send(embed=embed)

    @commands.command(aliases=["exit"])
    async def quit(self, ctx):
        if self.dictionary[ctx.guild.id]['voice_client'] is not None:
            await self.dictionary[ctx.guild.id]['voice_client'].disconnect()
            self.dictionary[ctx.guild.id]['voice_client'] = None
            self.dictionary[ctx.guild.id]['now_playing_song'] = None
            self.dictionary[ctx.guild.id]['song_queue'] = []
            await self.clear_presence(ctx)
            embed = discord.Embed(title="Goodbye! :wave:", url="https://f.chulte.de", color=0x00ffcc)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="I need to be in a channel to leave! :thinking:",
                                  url="https://f.chulte.de",
                                  color=0x00ffcc
                                  )
            await ctx.send(embed=embed)

    @commands.command(aliases=["empty"])
    async def clear(self, ctx):
        if len(self.dictionary[ctx.guild.id]['song_queue']) is not 0:
            self.dictionary[ctx.guild.id]['song_queue'] = []
            embed = discord.Embed(title="Cleared the Queue. :cloud:", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="The Playlist was already empty! :cloud:", color=0x00ffcc,
                                  url="https://f.chulte.de")
            await ctx.send(embed=embed)

    @commands.command(aliases=["mixer"])
    async def shuffle(self, ctx):
        if len(self.dictionary[ctx.guild.id]['song_queue']) > 0:
            random.shuffle(self.dictionary[ctx.guild.id]['song_queue'])
            embed = discord.Embed(title="Shuffled! :twisted_rightwards_arrows:", color=0x00ffcc,
                                  url="https://f.chulte.de")
            await ctx.send(embed=embed)
            await self.preload_next(ctx)

    @commands.command(aliases=["yeehee"])
    async def stop(self, ctx):
        dictionary = self.dictionary
        if dictionary[ctx.guild.id]['voice_client'] is not None:
            dictionary[ctx.guild.id]['song_queue'] = []
            dictionary[ctx.guild.id]['now_playing_song'] = None
            dictionary[ctx.guild.id]['voice_client'].stop()
            link = await self.youtube.youtube_url("https://www.youtube.com/watch?v=siLkbdVxntU")
            source = discord.FFmpegPCMAudio(link['stream'], executable="ffmpeg",
                                            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5")
            dictionary[ctx.guild.id]['voice_client'].play(source)
            if dictionary[ctx.guild.id]['voice_client'] is not None \
                    and dictionary[ctx.guild.id]['voice_client'].is_playing():
                embed = discord.Embed(title="Music Stopped! 🛑", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title=":thinking: The Bot isn't connected. :thinking:", color=0x00ffcc,
                                  url="https://f.chulte.de")
            await ctx.send(embed=embed)

    @commands.command(aliases=[])
    async def chars(self, ctx, first=None, last=None):
        if first is None:
            full, empty = await self.mongo.get_chars(ctx.guild.id)
            embed = discord.Embed(
                title="You are currently using **" + full + "** for 'full' and **" + empty + "** for 'empty'",
                color=0x00ffcc)
            embed.add_field(name="Syntax to add:",
                            value=".chars <full> <empty> \n"
                                  "Useful Website: https://changaco.oy.lc/unicode-progress-bars/"
                            )
            await ctx.send(embed=embed)
            return
        elif first == "reset" and last is None:
            await self.mongo.set_chars(ctx.guild.id, '█', '░')
            embed = discord.Embed(title="Characters reset to: Full: **█** and Empty: **░**", color=0x00ffcc)
            await ctx.send(embed=embed)
        elif last is None:
            embed = discord.Embed(title="You need to provide 2 Unicode Characters separated with a blank space.",
                                  color=0x00ffcc)
            await ctx.send(embed=embed)
            return
        if len(first) > 1 or len(last) > 1:
            embed = discord.Embed(title="The characters have a maximal length of 1.", color=0x00ffcc)
            await ctx.send(embed=embed)
            return
        await self.mongo.set_chars(ctx.guild.id, first, last)
        embed = discord.Embed(title="The characters got updated! Full: **" + first + "**, Empty: **" + last + "**",
                              color=0x00ffcc)
        await ctx.send(embed=embed)

    @commands.command(aliases=["halteein"])
    async def pause(self, ctx):
        dictionary = self.dictionary
        if dictionary[ctx.guild.id]['now_playing_song']['is_paused'] is True:
            embed = discord.Embed(title="Already Paused.", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed)
        if dictionary[ctx.guild.id]['voice_client'] is not None:
            try:
                dictionary[ctx.guild.id]['voice_client'].pause()
                embed = discord.Embed(title="Paused! ⏸", color=0x00ffcc, url="https://f.chulte.de")
                message = await ctx.send(embed=embed)
                dictionary[ctx.guild.id]['now_playing_song']['pause_time'] = int(time.time())
                dictionary[ctx.guild.id]['now_playing_song']['is_paused'] = True
                await asyncio.sleep(5)
                await message.delete()
                await ctx.message.delete()
            except Exception as e:
                print(e)
                embed = discord.Embed(title=":thinking: Nothing is playing... :thinking:", color=0x00ffcc,
                                      url="https://f.chulte.de")
                await ctx.send(embed=embed)

    @commands.command(aliases=['next', 'müll', 's'])
    async def skip(self, ctx, count='1'):
        try:
            count = int(count)
        except ValueError:
            embed = discord.Embed(title='Please provide a valid number.', url='https://f.chulte.de', color=0x00ffcc)
            await ctx.send(embed=embed)
            return
        dictionary = self.dictionary
        if dictionary[ctx.guild.id]['voice_client'] is not None:
            if dictionary[ctx.guild.id]['now_playing_song'] is not None:
                if count == 1:
                    embed = discord.Embed(title="Skipped! :track_next:", color=0x00ffcc, url="https://f.chulte.de")
                    await ctx.send(embed=embed, delete_after=10)
                    dictionary[ctx.guild.id]['voice_client'].stop()
                    if len(dictionary[ctx.guild.id]["song_queue"]) == 0:
                        dictionary[ctx.guild.id]['now_playing_song'] = None
                elif count < 1:
                    embed = discord.Embed(title='Please provide a valid number.', url='https://f.chulte.de',
                                          color=0x00ffcc)
                    await ctx.send(embed=embed)
                    return
                else:
                    if count > len(dictionary[ctx.guild.id]['song_queue']):
                        embed = discord.Embed(title='Skipped ' + str(len(dictionary[ctx.guild.id]['song_queue'])) +
                                                    ' Tracks! :track_next:', url='https://f.chulte.de', color=0x00ffcc)
                        await ctx.send(embed=embed)
                        dictionary[ctx.guild.id]['song_queue'] = []
                        dictionary[ctx.guild.id]['voice_client'].stop()
                        dictionary[ctx.guild.id]['now_playing_song'] = None
                    else:
                        dictionary[ctx.guild.id]['song_queue'] = dictionary[ctx.guild.id]['song_queue'][count - 1:]
                        dictionary[ctx.guild.id]['voice_client'].stop()
                        embed = discord.Embed(title='Skipped ' + str(count) + ' Tracks! :track_next:',
                                              url='https://f.chulte.de', color=0x00ffcc)
                        await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Nothing is playing right now!", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed=embed, delete_after=10)
        else:
            embed = discord.Embed(title="Not connected!", color=0x00ffcc, url="https://f.chulte.de")
            await ctx.send(embed=embed, delete_after=10)
        await asyncio.sleep(10)
        await ctx.message.delete()

    @commands.command(aliases=["unpause"])
    async def resume(self, ctx):
        dictionary = self.dictionary
        if dictionary[ctx.guild.id]['voice_client'] is not None:
            try:
                if 'pause_time' in dictionary[ctx.guild.id]['now_playing_song']:
                    dictionary[ctx.guild.id]['now_playing_song']['pause_duration'] += int(time.time()) - \
                                                                                      self.dictionary[ctx.guild.id][
                                                                                          'now_playing_song'][
                                                                                          'pause_time']
                    dictionary[ctx.guild.id]['now_playing_song']['is_paused'] = False
                dictionary[ctx.guild.id]['voice_client'].resume()
                embed = discord.Embed(title="Unpaused! ⏯", color=0x00ffcc, url="https://f.chulte.de")
                await ctx.send(embed=embed)
            except Exception as e:
                print('resume_nothing_running', e)
                embed = discord.Embed(title=":thinking: Nothing is running... :thinking:", color=0x00ffcc,
                                      url="https://f.chulte.de")
                await ctx.send(embed=embed)

    @commands.command()
    async def reset(self, ctx):
        if self.dictionary[ctx.guild.id]['voice_client'] is not None:
            await self.dictionary[ctx.guild.id]['voice_client'].disconnect()
        if ctx.guild.id not in self.dictionary:
            self.dictionary[ctx.guild.id] = dict()
        self.dictionary[ctx.guild.id]['song_queue'] = []
        self.dictionary[ctx.guild.id]['voice_client'] = None
        self.dictionary[ctx.guild.id]['voice_channel'] = None
        self.dictionary[ctx.guild.id]['now_playing_song'] = None
        embed = discord.Embed(
            title="I hope this resolved your issues. :smile: Click me if you want to file a bug report.",
            color=0x00ffcc, url="https://github.com/tooxo/Geiler-Musik-Bot/issues/new")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(DiscordBot(bot))
