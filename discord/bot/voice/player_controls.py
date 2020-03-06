import asyncio
import collections
import random
from os import environ

import discord
from discord.ext import commands
from discord.ext.commands import Cog

from bot.type.guild import Guild
from bot.type.queue import Queue
from bot.voice.checks import Checks


class PlayerControls(Cog, name="Player Controls"):
    def __init__(self, bot, parent):
        self.bot = bot
        self.parent = parent
        self.guilds = self.parent.guilds

    @commands.check(Checks.manipulation_checks)
    @commands.command(aliases=["exit"])
    async def quit(self, ctx):
        """
        Disconnects the bot.
        :param ctx:
        :return:
        """
        self.parent.guilds[ctx.guild.id].now_playing = None
        self.parent.guilds[ctx.guild.id].song_queue = Queue()
        await self.parent.clear_presence(ctx)
        await self.parent.guilds[ctx.guild.id].voice_client.disconnect()
        self.parent.guilds[ctx.guild.id].voice_client = None
        await self.parent.send_embed_message(ctx, "Goodbye! :wave:")

    @commands.check(Checks.manipulation_checks)
    @commands.command(aliases=["empty"])
    async def clear(self, ctx):
        """
        Clears the queue.
        :param ctx:
        :return:
        """
        if self.parent.guilds[ctx.guild.id].song_queue.qsize() != 0:
            self.parent.guilds[ctx.guild.id].song_queue.clear()
            await self.parent.send_embed_message(
                ctx, "Cleared the Queue. :cloud:"
            )
        else:
            await self.parent.send_error_message(
                ctx, "The Queue was already empty! :cloud:"
            )

    @commands.check(Checks.manipulation_checks)
    @commands.command(aliases=["mixer"])
    async def shuffle(self, ctx):
        """
        Shuffles the queue.
        :param ctx:
        :return:
        """
        if self.parent.guilds[ctx.guild.id].song_queue.qsize() > 0:
            random.shuffle(self.parent.guilds[ctx.guild.id].song_queue.queue)
            await self.parent.send_embed_message(
                ctx, "Shuffled! :twisted_rightwards_arrows:"
            )
        else:
            await self.parent.send_error_message(
                ctx, "The queue is empty. :cloud:"
            )

    @commands.check(Checks.manipulation_checks)
    @commands.check(Checks.voice_client_check)
    @commands.command(aliases=["yeehee"])
    async def stop(self, ctx):
        """
        Stops playback.
        :param ctx:
        :return:
        """
        self.parent.guilds[ctx.guild.id].song_queue.clear()
        self.parent.guilds[ctx.guild.id].now_playing = None
        self.parent.guilds[ctx.guild.id].voice_client.stop()
        await self.parent.send_embed_message(
            ctx, "Music Stopped! :octagonal_sign:"
        )

    @commands.check(Checks.manipulation_checks)
    @commands.check(Checks.song_playing_check)
    @commands.command(aliases=["halteein"])
    async def pause(self, ctx):
        """
        Pauses playback.
        :param ctx:
        :return:
        """
        if self.parent.guilds[ctx.guild.id].voice_client.is_paused():
            await self.parent.send_error_message(ctx, "Already Paused.")
            return
        if self.parent.guilds[ctx.guild.id].voice_client is not None:
            self.parent.guilds[ctx.guild.id].voice_client.pause()
            message = await self.parent.send_embed_message(
                ctx, "Paused! :pause_button:"
            )
            await asyncio.sleep(5)
            await message.delete()
            await ctx.message.delete()

    @commands.check(Checks.manipulation_checks)
    @commands.command(aliases=["next", "müll", "s", "n", "nein"])
    async def skip(self, ctx, count="1"):
        """
        Skips a song.
        :param ctx:
        :param count:
        :return:
        """
        try:
            count = int(count)
        except ValueError:
            await self.parent.send_error_message(
                ctx, "Please provide a valid number."
            )
            return
        if self.parent.guilds[ctx.guild.id].voice_client is not None:
            if self.parent.guilds[ctx.guild.id].now_playing is not None:
                if count == 1:
                    await self.parent.send_embed_message(
                        ctx, "Skipped! :track_next:", delete_after=10
                    )
                    self.parent.guilds[ctx.guild.id].voice_client.stop()
                elif count < 1:
                    await self.parent.send_error_message(
                        ctx, "Please provide a valid number."
                    )
                    return
                else:
                    if (
                        count
                        > self.parent.guilds[ctx.guild.id].song_queue.qsize()
                    ):
                        await self.parent.send_embed_message(
                            ctx,
                            "Skipped "
                            + str(
                                self.parent.guilds[
                                    ctx.guild.id
                                ].song_queue.qsize()
                            )
                            + " Tracks! :track_next:",
                        )
                        self.parent.guilds[ctx.guild.id].voice_client.stop()
                    else:

                        queue = self.parent.guilds[
                            ctx.guild.id
                        ].song_queue.queue

                        self.parent.guilds[
                            ctx.guild.id
                        ].song_queue.queue = collections.deque(
                            list(queue)[(count - 1) :]
                        )
                    self.parent.guilds[ctx.guild.id].voice_client.stop()
                    await self.parent.send_embed_message(
                        ctx, "Skipped " + str(count) + " Tracks! :track_next:"
                    )
            else:
                await self.parent.send_error_message(
                    ctx, "Nothing is playing right now!", delete_after=10
                )

        else:
            await self.parent.send_error_message(
                ctx, "Not connected!", delete_after=10
            )

        await asyncio.sleep(10)
        await ctx.message.delete()

    @commands.check(Checks.manipulation_checks)
    @commands.check(Checks.voice_client_check)
    @commands.check(Checks.song_playing_check)
    @commands.command(aliases=["back"])
    async def prev(self, ctx):
        """
        Jumps back a song.
        :param ctx:
        :return:
        """

        _song_queue: Queue = self.parent.guilds[ctx.guild.id].song_queue
        _voice_client = self.parent.guilds[ctx.guild.id].voice_client
        if not _song_queue.back_queue.__len__() == 0:
            last_song = _song_queue.get_last()
            _song_queue.queue.appendleft(last_song)
            _voice_client.stop()

    @commands.check(Checks.manipulation_checks)
    @commands.check(Checks.song_playing_check)
    @commands.check(Checks.voice_client_check)
    @commands.command(aliases=["unpause"])
    async def resume(self, ctx):
        """
        Resumes playback.
        :param ctx:
        :return:
        """
        if self.parent.guilds[ctx.guild.id].voice_client.is_paused():
            self.parent.guilds[ctx.guild.id].voice_client.resume()
            await self.parent.send_embed_message(ctx, "Unpaused! :play_pause:")
        else:
            await self.parent.send_error_message(ctx, "Not Paused.")

    @commands.check(Checks.manipulation_checks)
    @commands.check(Checks.voice_client_check)
    @commands.command(aliases=[])
    async def seek(self, ctx, *, distance: str = ""):
        """
        Seeks in the song.
        :param ctx:
        :param distance:
        :return:
        """
        try:
            if distance == "":
                raise ValueError()
            parsed = int(distance)
        except ValueError:
            await self.parent.send_error_message(ctx, "Invalid value.")
            return  # shit
        if self.parent.guilds[ctx.guild.id].voice_client.is_playing():
            if not self.parent.guilds[ctx.guild.id].voice_client.is_paused():
                self.parent.guilds[ctx.guild.id].voice_client.seek(
                    song=self.parent.guilds[ctx.guild.id].now_playing,
                    volume=self.parent.guilds[ctx.guild.id].volume,
                    seconds_to_seek=parsed,
                )
                return await self.parent.send_embed_message(
                    ctx, f"**Seeked {parsed} seconds forward.**"
                )
            return await self.parent.send_error_message(
                ctx, "Can't do this while paused."
            )
        return await self.parent.send_error_message(
            ctx, "Can't do this while nothing is playing."
        )

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        """
        Shows the queue.
        :param ctx:
        :return:
        """
        use_embeds = environ.get("USE_EMBEDS", "True") == "True"
        no_embed_string = ""
        embed = discord.Embed(colour=0x00FFCC)
        if use_embeds:
            if self.parent.guilds[ctx.guild.id].now_playing is not None:
                embed.add_field(
                    name="**Currently Playing ...**",
                    value="`"
                    + self.parent.guilds[ctx.guild.id].now_playing.title
                    + "`\n",
                    inline=False,
                )
            else:
                embed.add_field(
                    name="**Currently Playing...**",
                    value="Nothing.\n",
                    inline=False,
                )
        else:
            no_embed_string += "**Currently Playing ...**" + "\n"
            try:
                no_embed_string += (
                    "`"
                    + self.parent.guilds[ctx.guild.id].now_playing.title
                    + "`\n"
                )
            except AttributeError:
                no_embed_string += "Nothing.\n"

        if len(self.parent.guilds[ctx.guild.id].song_queue.queue) > 0:
            _t = ""
            for x in range(0, 9, 1):
                try:

                    if (
                        self.parent.guilds[ctx.guild.id].song_queue.queue[x]
                        is not None
                    ):

                        _t += f"`({x+1})` `{self.parent.guilds[ctx.guild.id].song_queue.queue[x].title}`\n"

                    elif (
                        self.parent.guilds[ctx.guild.id]
                        .song_queue.queue[x]
                        .link
                        is not None
                    ):

                        _t += f"`({x+1})` `{self.parent.guilds[ctx.guild.id].song_queue.queue[x].link}`\n"
                    else:
                        break
                except (IndexError, KeyError, AttributeError, TypeError):
                    break

            if (len(self.parent.guilds[ctx.guild.id].song_queue.queue) - 9) > 0:
                _t += (
                    "`(+)` `"
                    + str(
                        len(self.parent.guilds[ctx.guild.id].song_queue.queue)
                        - 9
                    )
                    + " Tracks...`"
                )
            if use_embeds:
                embed.add_field(name="**Coming up:**", value=_t, inline=False)
            else:
                no_embed_string += "**Coming up:**\n"
                no_embed_string += _t
        else:
            if use_embeds:
                embed.add_field(
                    name="**Coming up:**",
                    value="Nothing in Queue. Use .play to add something.",
                    inline=False,
                )
            else:
                no_embed_string += "**Coming up:**\n"
                no_embed_string += (
                    "Nothing in Queue. Use .play to add something."
                )

        if use_embeds:
            await ctx.send(embed=embed)
        else:
            await ctx.send(content=no_embed_string)

    @commands.command()
    async def announce(self, ctx, new_status: str = None):
        """
        Controls song announcements
        :param ctx:
        :param new_status:
        :return:
        """
        guild: Guild = self.guilds[ctx.guild.id]
        positives = ("on", "true", "ja")
        negatives = ("off", "false", "nein")
        if new_status:
            if new_status.lower() not in (*positives, *negatives):
                return await self.parent.send_error_message(
                    ctx, "Invalid Argument."
                )
            if new_status.lower() in positives:
                guild.announce = True
            else:
                guild.announce = False
        else:
            guild.toggle_announce()
        asyncio.ensure_future(
            self.parent.mongo.set_announce(ctx.guild.id, guild.announce)
        )
        message = (
            f"{'Enabled' if guild.announce else 'Disabled'} song announcements."
        )
        return await self.parent.send_embed_message(ctx, message)
