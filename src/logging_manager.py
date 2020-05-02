"""
LoggingManager
"""
import logging
from inspect import getframeinfo, stack


class LoggingManager:
    """
    LoggingManager
    """

    def __init__(self) -> None:
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("LOG")
        self.handler = logging.StreamHandler()
        self.formatter = logging.Formatter(
            "%(asctime)s %(levelname)-6s %(message)s"
        )
        self.handler.setFormatter(self.formatter)
        self.logger.propagate = False
        if not self.logger.handlers:
            self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)

    def info(self, message: str) -> None:
        """
        Log INFO
        @param message: 
        @return: 
        """
        self.logger.info(message)

    def debug(self, message: str) -> None:
        """
        Log DEBUG
        @param message: 
        @return: 
        """
        self.logger.debug(message)

    def warning(self, message: str) -> None:
        """
        Log WARNING
        @param message: 
        @return: 
        """
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """
        Log ERROR
        @param message: 
        @return: 
        """
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """
        Log CRITIAL
        @param message: 
        @return: 
        """
        self.logger.critical(message)


def debug_info(message: str) -> str:
    """
    Append Debug Info to a string.
    @param message:
    @return:
    """
    caller = getframeinfo(stack()[1][0])
    return "%s:%d - %s" % (caller.filename, caller.lineno, message)
