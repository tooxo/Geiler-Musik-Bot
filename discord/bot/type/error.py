from .errors import Errors


class Error:
    def __init__(self, error: bool, reason: str = Errors.default):
        self.error = error
        self.reason = reason
        self.link = ""
