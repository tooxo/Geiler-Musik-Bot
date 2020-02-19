from discord.ext.commands import CommandError


class NotSameChannel(CommandError):
    pass


class BotNotConnected(CommandError):
    pass


class UserNotConnected(CommandError):
    pass


class NothingPlaying(CommandError):
    pass
