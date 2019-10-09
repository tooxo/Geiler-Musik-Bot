from asyncio import Queue
from variable_store import Errors


class Song:
    def __init__(self, song=None):
        if song:
            self.title = song.title
            self.term = song.term
            self.id = song.id
            self.link = song.link
            self.stream = song.stream
            self.duration = song.duration
            self.loadtime = song.loadtime
            self.error = song.error
            self.user = song.user
            self.start_time = song.start_time
            self.is_paused = song.is_paused
            self.pause_duration = song.pause_duration
            self.image_url = song.image_url
            self.pause_time = song.pause_time
        else:
            self.title = None
            self.term = None
            self.id = None
            self.link = None
            self.stream = None
            self.duration = None
            self.loadtime = None
            self.thumbnail = None
            self.error = Error(False)
            self.user = None
            self.start_time = None
            self.is_paused = False
            self.pause_duration = 0
            self.image_url = None
            self.pause_time = None

    @property
    def image(self):
        if self.image_url is not None and self.image_url != "":
            return self.image_url
        if self.thumbnail is not None and self.thumbnail != "":
            return self.thumbnail
        return None


class Guild:
    def __init__(self):
        self.voice_client = None
        self.voice_channel = None
        self.song_queue = Queue()
        self.now_playing_message = None
        self.now_playing = None
        self.volume = 0.5


class Error:
    def __init__(self, error: bool, reason: str = Errors.default):
        self.error = error
        self.reason = reason
        self.link = ""


class SpotifyObj:
    def __init__(self, title: str, image_url: str):
        self.title = title
        self.image_url = image_url
