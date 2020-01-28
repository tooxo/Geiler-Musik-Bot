import discord.ext.commands


class Checks:
    def __init__(self, bot, parent):
        self.parent = parent
        self.bot = bot

    async def same_channel_check(self, ctx: discord.ext.commands.Context):
        """
        checks if the user is in the same channel
        :param ctx: context
        :return:
        """
        if ctx.me.voice is not None:
            if ctx.guild.me.voice.channel != ctx.author.voice.channel:
                await self.parent.send_error_message(
                    ctx, "You need to be in the same channel as the bot."
                )
                return False
        return True

    async def user_connection_check(self, ctx):
        try:
            if not hasattr(ctx.author.voice, "channel"):
                await self.parent.send_error_message(
                    ctx, "You need to be in a channel."
                )
                return False
        except AttributeError:
            return False
        return True

    async def bot_connection_check(self, ctx):
        if ctx.guild.me.voice is None:
            await self.parent.send_error_message(ctx, "The bot isn't connected.")
            return False
        return True

    async def manipulation_checks(self, ctx):
        return (
            await self.bot_connection_check(ctx)
            and await self.user_connection_check(ctx)
            and await self.same_channel_check(ctx)
        )

    async def song_playing_check(self, ctx):
        if self.parent.guilds[ctx.guild.id].now_playing is None:
            await self.parent.send_error_message(ctx, "Nothing is playing right now!")
            return False
        return True
