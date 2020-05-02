"""
Exceptions
"""
from discord.ext.commands import CommandError


class NotSameChannel(CommandError):
    """
    Raised, if the user is not in the same channel as the bot while executing
    a channel dependent command
    """


class BotNotConnected(CommandError):
    """
    Raised, if the bot is not connected while executing a channel dependent
    command
    """


class UserNotConnected(CommandError):
    """
    Raised, if the user is not connected while executing a channel dependent
    command
    """


class NothingPlaying(CommandError):
    """
    Raised, if no song is playing while the user executes a command relying
    on a song playing.
    """


class BasicError(CommandError):
    """
    Basic Error class
    """


class NoResultsFound(BasicError):
    """
    Raised, when no results were found during song aggregation
    """


class BackendDownException(BasicError):
    """
    Raised, when the backend is down or not started, while the user tries to
    execute a command.
    """


class NoNodeReadyException(BackendDownException):
    """
    Raised, when no node is currently connected or in auth process, while the
    user requests something node dependent
    """


class InfoExtractionException(BasicError):
    """
    Raised, when information extraction for a song or a playlist fails
    """


class PlaylistExtractionException(InfoExtractionException):
    """
    Raised, when information extraction for a playlist fails
    """


class SongExtractionException(InfoExtractionException):
    """
    Raised, when information extraction for a song fails
    """
