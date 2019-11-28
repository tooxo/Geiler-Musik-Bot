import asyncio
import discord
import time
import logging_manager
import aiohttp


class NowPlayingMessage:
    def __init__(
        self,
        song=None,
        ctx=None,
        message=None,
        full=None,
        empty=None,
        discord_music=None,
    ):
        self.discord_music = discord_music
        self.log = logging_manager.LoggingManager()
        self.song = song
        self._stop = False
        self.ctx = ctx
        self.message = message
        self.full = full
        self.empty = empty
        if self.song.title == "_" or self.song.title is None:
            self.title = "`" + self.song.term + "`"
        else:
            self.title = "`" + self.song.title + "`"

    async def send(self):
        embed = discord.Embed(title=self.title, color=0x00FFCC, url=self.song.link)
        embed.set_author(name="Currently Playing:")
        embed.add_field(name="░░░░░░░░░░░░░░░░░░░░░░░░░", value=" 0%")
        await self.message.edit(embed=embed)

    async def update(self):
        if self._stop is True:
            return
        try:
            if (
                self.discord_music.dictionary[self.ctx.guild.id].now_playing.is_paused
                is False
            ):
                now_time = (
                    int(time.time())
                    - self.discord_music.dictionary[
                        self.ctx.guild.id
                    ].now_playing.start_time
                    - self.discord_music.dictionary[
                        self.ctx.guild.id
                    ].now_playing.pause_duration
                )
                finish_second = int(
                    self.discord_music.dictionary[
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
                            self.discord_music.dictionary[
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
                """
                try:
                    if self.song.image is not None:
                        embed2.set_thumbnail(url=self.song.image)
                        # self.dictionary[ctx.guild.id]['now_playing_song']['image_url'] = ""
                except Exception as e:
                    self.log.error(logging_manager.debug_info(str(e)))
                """
                try:
                    await self.message.edit(embed=embed2)
                except (discord.NotFound, TypeError):
                    return
            else:
                if self._stop is False:
                    await asyncio.sleep(0.1)
                    await self.update()
        except (TypeError, AttributeError, aiohttp.ServerDisconnectedError) as e:
            return
        await asyncio.sleep(1)
        if self._stop is False:
            await self.update()

    async def stop(self):
        self._stop = True
        embed = discord.Embed(
            title="_`" + self.song.title + "`_", color=0x00FF00, url=self.song.link
        )
        await self.message.edit(embed=embed)
