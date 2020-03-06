from typing import Dict
from urllib.parse import quote

from discord.ext import commands

from bot.type.guild import Guild
from bot.type.queue import Queue
from bot.type.song import Song


def check_tts_requirements(ctx, *args, **kwargs):
    self = ctx.cog
    if self.guilds[ctx.guild.id].now_playing:
        return False
    return True


class TTS(commands.Cog):
    def __init__(self, bot, parent):
        self.tts_base_url = "https://translate.google.com/translate_tts?ie=UTF-8&tl=de-DE&client=tw-ob&q="
        self.bot = bot
        self.parent = parent
        self.guilds: Dict[Guild] = self.parent.guilds
        self.send_embed_message = self.parent.send_embed_message
        self.tts_queue = Queue()

    async def next_tts(self, ctx):
        if not self.guilds[ctx.guild.id].voice_client:
            return
        if not self.tts_queue.empty():
            song = await self.tts_queue.get()
            self.guilds[ctx.guild.id].voice_client.play(
                song, self.guilds[ctx.guild.id].volume
            )
            self.guilds[ctx.guild.id].voice_client.set_after(self.next_tts, ctx)

    @commands.command(hidden=True)
    @commands.check(check_tts_requirements)
    async def tts(self, ctx: commands.Context, *, text: str):
        quoted = quote(text)
        if await self.parent.player.join_check(ctx):
            if await self.parent.player.join_channel(ctx):
                song: Song = Song.from_dict(
                    {
                        "guild_id": ctx.guild.id,
                        "stream": f"{self.tts_base_url}{quoted}",
                        "youtube_stream": "",
                        "cipher": "",
                    }
                )
                self.tts_queue.put_nowait(song)
                if not self.guilds[ctx.guild.id].voice_client.is_playing():
                    await self.next_tts(ctx)

    @tts.error
    async def tts_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await self.send_embed_message(
                ctx,
                "Currently not supported while playing music. Stop the music first.",
                delete_after=None,
                url=None,
            )
        if isinstance(error, commands.MissingRequiredArgument):
            await self.send_embed_message(
                ctx, "You need to enter text.", delete_after=None, url=None
            )
