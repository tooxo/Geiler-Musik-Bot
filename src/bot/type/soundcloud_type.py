"""
SoundCloudType
"""
import re

from bot.type.variable_store import VariableStore


class SoundCloudType:
    """
    SoundCloudType
    """

    def __init__(self, url) -> None:
        self.url = url

    @property
    def valid(self) -> bool:
        """
        Check if the provided url is valid
        @return:
        """
        if (
            re.match(VariableStore.soundcloud_url_pattern, self.url) is not None
            or re.match(VariableStore.soundcloud_sets_pattern, self.url)
            is not None
        ):
            return True
        return False
