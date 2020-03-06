import discord.ext.commands

from bot.type.exceptions import (
    BotNotConnected,
    NothingPlaying,
    NotSameChannel,
    UserNotConnected,
)


class Checks:
    def __init__(self, bot, parent):
        self.parent = parent
        self.bot = bot

    @staticmethod
    def same_channel_check(
        ctx: discord.ext.commands.Context, *args, **kwargs
    ) -> bool:
        if ctx.me.voice is not None:
            if ctx.guild.me.voice.channel != ctx.author.voice.channel:
                raise NotSameChannel()
        return True

    @staticmethod
    def user_connection_check(ctx: discord.ext.commands.Context) -> bool:
        try:
            if not hasattr(ctx.author.voice, "channel"):
                raise UserNotConnected()
        except AttributeError:
            raise UserNotConnected()
        return True

    @staticmethod
    def bot_connection_check(ctx):
        if ctx.guild.me.voice is not None:
            return True
        raise BotNotConnected()

    @staticmethod
    def manipulation_checks(ctx, *args, **kwargs):
        if not Checks.bot_connection_check(ctx):
            return False
        if not Checks.user_connection_check(ctx):
            return False
        if not Checks.same_channel_check(ctx):
            return False
        return True

    @staticmethod
    def song_playing_check(ctx, *args, **kwargs):
        if ctx.cog.guilds[ctx.guild.id].now_playing is None:
            raise NothingPlaying()
        return True

    @staticmethod
    def voice_client_check(ctx, *args, **kwargs):
        if ctx.cog.parent.guilds[ctx.guild.id].voice_client:
            return True
        raise BotNotConnected()
