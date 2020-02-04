import re

from bot.type.variable_store import VariableStore


class SoundCloudType:
    def __init__(self, url):
        self.url = url

    @property
    def valid(self):
        if (
            re.match(VariableStore.soundcloud_url_pattern, self.url) is not None
            or re.match(VariableStore.soundcloud_sets_pattern, self.url)
            is not None
        ):
            return True
        return False
