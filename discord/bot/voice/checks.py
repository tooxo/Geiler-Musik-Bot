"""
Checks
"""
from typing import TYPE_CHECKING

import discord.ext.commands

from bot.type.exceptions import (
    BotNotConnected,
    NothingPlaying,
    NotSameChannel,
    UserNotConnected,
)

if TYPE_CHECKING:
    from bot.discord_music import DiscordBot


class Checks:
    """
    Checks
    """

    def __init__(self, bot: discord.ext.commands.Bot, parent: "DiscordBot"):
        self.parent = parent
        self.bot = bot

    # noinspection PyUnusedLocal
    @staticmethod
    def same_channel_check(
        ctx: discord.ext.commands.Context,
        *args,  # pylint: disable=unused-argument
        **kwargs  # pylint: disable=unused-argument
    ) -> bool:
        """
        Checks if user and bot are in the same channel.
        @param ctx:
        @param args:
        @param kwargs:
        @return:
        """
        if ctx.me.voice is not None:
            if ctx.guild.me.voice.channel != ctx.author.voice.channel:
                raise NotSameChannel()
        return True

    @staticmethod
    def user_connection_check(ctx: discord.ext.commands.Context) -> bool:
        """
        Checks if user is connected
        @param ctx:
        @return:
        """
        try:
            if not hasattr(ctx.author.voice, "channel"):
                raise UserNotConnected()
        except AttributeError:
            raise UserNotConnected()
        return True

    @staticmethod
    def bot_connection_check(ctx: discord.ext.commands.Context) -> bool:
        """
        Checks if the bot is connected
        @param ctx:
        @return:
        """
        if ctx.guild.me.voice is not None:
            return True
        raise BotNotConnected()

    # noinspection PyUnusedLocal
    @staticmethod
    def manipulation_checks(
        ctx: discord.ext.commands.Context,
        *args,  # pylint: disable=unused-argument
        **kwargs  # pylint: disable=unused-argument
    ) -> bool:
        """
        Checks if a user is permitted to change something about the bot playing music right now
        @param ctx:
        @param args:
        @param kwargs:
        @return:
        """
        if not Checks.bot_connection_check(ctx):
            return False
        if not Checks.user_connection_check(ctx):
            return False
        if not Checks.same_channel_check(ctx):
            return False
        return True

    # noinspection PyUnusedLocal
    @staticmethod
    def song_playing_check(
        ctx: discord.ext.commands.Context,
        *args,  # pylint: disable=unused-argument
        **kwargs  # pylint: disable=unused-argument
    ):
        """
        Check is a song is currently playing
        @param ctx:
        @param args:
        @param kwargs:
        @return:
        """
        if ctx.cog.guilds[ctx.guild.id].now_playing is None:
            raise NothingPlaying()
        return True

    # noinspection PyUnusedLocal
    @staticmethod
    def voice_client_check(
        ctx: discord.ext.commands.Context,
        *args,  # pylint: disable=unused-argument
        **kwargs  # pylint: disable=unused-argument
    ):
        """
        Check if the bot is connected.
        @param ctx:
        @param args:
        @param kwargs:
        @return:
        """
        if ctx.cog.parent.guilds[ctx.guild.id].voice_client:
            return True
        raise BotNotConnected()
