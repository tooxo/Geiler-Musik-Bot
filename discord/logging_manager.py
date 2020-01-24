import logging
from inspect import getframeinfo, stack


class LoggingManager:
    def __init__(self):
        logging.basicConfig(level=logging.WARNING)
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

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message):
        self.logger.error(message)

    def critical(self, message):
        pass


def debug_info(message):
    caller = getframeinfo(stack()[1][0])
    return "%s:%d - %s" % (caller.filename, caller.lineno, message)
