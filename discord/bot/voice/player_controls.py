import asyncio
import collections
import random
from os import environ

import discord
from bot.type.queue import Queue
from discord.ext import commands
from discord.ext.commands import Cog


class PlayerControls(Cog):
    def __init__(self, bot, parent):
        self.bot = bot
        self.parent = parent

    @commands.command(aliases=["exit"])
    async def quit(self, ctx):
        if not await self.parent.control_check.manipulation_checks(ctx):
            return
        self.parent.guilds[ctx.guild.id].now_playing = None
        self.parent.guilds[ctx.guild.id].song_queue = Queue()
        await self.parent.clear_presence(ctx)
        await self.parent.guilds[ctx.guild.id].voice_client.disconnect()
        self.parent.guilds[ctx.guild.id].voice_client = None
        await self.parent.send_embed_message(ctx, "Goodbye! :wave:")

    @commands.command(aliases=["empty"])
    async def clear(self, ctx):
        if not await self.parent.control_check.manipulation_checks(ctx):
            return
        if self.parent.guilds[ctx.guild.id].song_queue.qsize() != 0:
            self.parent.guilds[ctx.guild.id].song_queue = Queue()
            await self.parent.send_embed_message(
                ctx, "Cleared the Queue. :cloud:"
            )
        else:
            await self.parent.send_error_message(
                ctx, "The Playlist was already empty! :cloud:"
            )

    @commands.command(aliases=["mixer"])
    async def shuffle(self, ctx):
        if not await self.parent.control_check.manipulation_checks(ctx):
            return
        if self.parent.guilds[ctx.guild.id].song_queue.qsize() > 0:
            random.shuffle(self.parent.guilds[ctx.guild.id].song_queue.queue)
            await self.parent.send_embed_message(
                ctx, "Shuffled! :twisted_rightwards_arrows:"
            )
        else:
            await self.parent.send_error_message(
                ctx, "The queue is empty. :cloud:"
            )

    @commands.command(aliases=["yeehee"])
    async def stop(self, ctx):
        if not await self.parent.control_check.manipulation_checks(ctx):
            return
        if self.parent.guilds[ctx.guild.id].voice_client is not None:
            self.parent.guilds[ctx.guild.id].song_queue = Queue()
            self.parent.guilds[ctx.guild.id].now_playing = None
            self.parent.guilds[ctx.guild.id].voice_client.stop()
            await self.parent.send_embed_message(
                ctx, "Music Stopped! :octagonal_sign:"
            )
        else:
            await self.parent.send_error_message(
                ctx, ":thinking: The Bot isn't connected. :thinking:"
            )

    @commands.command(aliases=["halteein"])
    async def pause(self, ctx):
        if not await self.parent.control_check.manipulation_checks(ctx):
            return
        if not await self.parent.control_check.song_playing_check(ctx):
            return
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

    @commands.command(aliases=["next", "müll", "s", "n", "nein"])
    async def skip(self, ctx, count="1"):
        if not await self.parent.control_check.manipulation_checks(ctx):
            return
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

    @commands.command(aliases=["unpause"])
    async def resume(self, ctx):
        if not await self.parent.control_check.manipulation_checks(ctx):
            return
        if not await self.parent.control_check.song_playing_check(ctx):
            return
        if self.parent.guilds[ctx.guild.id].voice_client is not None:
            if self.parent.guilds[ctx.guild.id].voice_client.is_paused():
                self.parent.guilds[ctx.guild.id].voice_client.resume()
                await self.parent.send_embed_message(
                    ctx, "Unpaused! :play_pause:"
                )
            else:
                await self.parent.send_error_message(ctx, "Not Paused.")

    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        numbers = [
            "`(1)`",
            "`(2)`",
            "`(3)`",
            "`(4)`",
            "`(5)`",
            "`(6)`",
            "`(7)`",
            "`(8)`",
            "`(9)`",
        ]
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

                        _t += (
                            numbers[x]
                            + " `"
                            + self.parent.guilds[ctx.guild.id]
                            .song_queue.queue[x]
                            .title
                            + "`\n"
                        )

                    elif (
                        self.parent.guilds[ctx.guild.id]
                        .song_queue.queue[x]
                        .link
                        is not None
                    ):

                        _t += (
                            numbers[x]
                            + " `"
                            + self.parent.guilds[ctx.guild.id]
                            .song_queue.queue[x]
                            .link
                            + "`\n"
                        )
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
