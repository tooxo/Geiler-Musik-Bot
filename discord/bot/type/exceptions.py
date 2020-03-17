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


class NoNodeReadyException(BackendDownException):
    pass


class InfoExtractionException(BasicError):
    """
    Raised, when information extraction for a song or a playlist fails
    """

    pass


class PlaylistExtractionException(InfoExtractionException):
    """
    Raised, when information extraction for a playlist fails
    """

    pass


class SongExtractionException(InfoExtractionException):
    """
    Raised, when information extraction for a song fails
    """
