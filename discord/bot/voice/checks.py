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

    # async def same_channel_check(self, ctx: discord.ext.commands.Context):
    #     """
    #     checks if the user is in the same channel
    #     :param ctx: context
    #     :return:
    #     """
    #     if ctx.me.voice is not None:
    #         if ctx.guild.me.voice.channel != ctx.author.voice.channel:
    #             await self.parent.send_error_message(
    #                 ctx, "You need to be in the same channel as the bot."
    #             )
    #             return False
    #     return True

    @staticmethod
    def same_channel_check(
        ctx: discord.ext.commands.Context, *args, **kwargs
    ) -> bool:
        if ctx.me.voice is not None:
            if ctx.guild.me.voice.channel != ctx.author.voice.channel:
                raise NotSameChannel()
        return True

    # async def user_connection_check(self, ctx):
    #     try:
    #         if not hasattr(ctx.author.voice, "channel"):
    #             await self.parent.send_error_message(
    #                 ctx, "You need to be in a channel."
    #             )
    #             return False
    #     except AttributeError:
    #         return False
    #     return True

    @staticmethod
    def user_connection_check(ctx: discord.ext.commands.Context) -> bool:
        try:
            if not hasattr(ctx.author.voice, "channel"):
                raise UserNotConnected()
        except AttributeError:
            raise UserNotConnected()
        return True

    # async def bot_connection_check(self, ctx):
    #     if ctx.guild.me.voice is None:
    #         await self.parent.send_error_message(
    #             ctx, "The bot isn't connected."
    #         )
    #         return False
    #     return True

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

    #  async def song_playing_check(self, ctx):
    #       if self.parent.guilds[ctx.guild.id].now_playing is None:
    #          await self.parent.send_error_message(
    #             ctx, "Nothing is playing right now!"
    #        )
    #       return False
    #  return True

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
