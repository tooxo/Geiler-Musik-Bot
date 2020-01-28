import asyncio
import time
import traceback
from os import environ

import aiohttp

import discord
import logging_manager
from bot.FFmpegPCMAudio import PCMVolumeTransformerB


class NowPlayingMessage:
    def __init__(
        self,
        ctx,
        message,
        song=None,
        full=None,
        empty=None,
        discord_music=None,
        voice_client: discord.VoiceClient = None,
    ):
        self.discord_music = discord_music
        self.log = logging_manager.LoggingManager()
        self.song = song
        self._stop = False
        self.ctx = ctx
        self.message: discord.Message = message
        self.full = full
        self.empty = empty
        if voice_client is not None:
            self.voice_client: discord.VoiceClient = voice_client
            self.source: PCMVolumeTransformerB = voice_client.source
        if self.song is not None:
            if self.song.title == "_" or self.song.title is None:
                self.title = "`" + self.song.term + "`"
            else:
                self.title = "`" + self.song.title + "`"
        self.no_embed_mode = environ.get("USE_EMBEDS", "True") == "False"

    def calculate_recurrences(self):
        """
        calculates if the message will update more than 75 times to stop on long songs
        :return: bool if too big
        """
        if hasattr(self.song, "duration"):
            recurrences = self.song.duration / 5
            if recurrences < 75:
                return True
        return False

    async def send(self):
        if self.song is None:
            return
        if not self.no_embed_mode:
            if self.calculate_recurrences():
                embed = discord.Embed(
                    title=self.title, color=0x00FFCC, url=self.song.link
                )
                embed.set_author(name="Currently Playing:")
                embed.add_field(name="░░░░░░░░░░░░░░░░░░░░░░░░░", value=" 0%")
                await self.message.edit(embed=embed)
                asyncio.ensure_future(self.update())
            else:
                embed = discord.Embed(
                    title=self.title, color=0x00FFCC, url=self.song.link
                )
                embed.set_author(name="Currently Playing:")
                await self.message.edit(embed=embed)

        else:
            await self.message.edit(content=self.title)

    async def update(self):
        if self._stop is True:
            return
        try:
            if not (self.voice_client.is_paused()):
                now_time = round(self.source.bytes_read / 192000)
                finish_second = int(
                    self.discord_music.guilds[
                        self.ctx.guild.id
                    ].now_playing.duration
                )
                description = (
                    "`"
                    + time.strftime("%H:%M:%S", time.gmtime(now_time))
                    + " / "
                    + time.strftime(
                        "%H:%M:%S",
                        time.gmtime(
                            self.discord_music.guilds[
                                self.ctx.guild.id
                            ].now_playing.duration
                        ),
                    )
                    + "`"
                )

                percentage = int((now_time / finish_second) * 100)

                if percentage > 100:
                    await self.stop()
                    return
                count = percentage / 4
                hashes = ""
                while count > 0:
                    hashes += self.full
                    count -= 1
                while len(hashes) < 25:
                    hashes += self.empty
                hashes += " " + str(percentage) + "%"

                embed2 = discord.Embed(
                    title=self.title, color=0x00FFCC, url=self.song.link
                )
                embed2.set_author(name="Currently Playing:")
                embed2.add_field(name=hashes, value=description)
                try:
                    await self.message.edit(embed=embed2)
                except (discord.NotFound, TypeError):
                    return
            else:
                if self._stop is False:
                    while self.voice_client.is_paused():
                        await asyncio.sleep(0.1)
                    await self.update()
        except (TypeError, AttributeError, aiohttp.ServerDisconnectedError) as e:
            return
        await asyncio.sleep(5)
        if self._stop is False:
            await self.update()

    async def stop(self):
        self._stop = True
        if self.song is None:
            await self.message.delete()
            return
        if not self.no_embed_mode:
            embed = discord.Embed(
                title="_`" + self.song.title + "`_", color=0x00FF00, url=self.song.link
            )
            await self.message.edit(embed=embed)
        else:
            await self.message.edit(content="_`" + self.song.title + "`_")
