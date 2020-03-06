from discord.ext.commands import CommandError
from .errors import Errors


class NotSameChannel(CommandError):
    pass


class BotNotConnected(CommandError):
    pass


class UserNotConnected(CommandError):
    pass


class NothingPlaying(CommandError):
    pass


class BasicError(CommandError):
    pass


class NoResultsFound(BasicError):
    pass


class BackendDownException(BasicError):
    pass
