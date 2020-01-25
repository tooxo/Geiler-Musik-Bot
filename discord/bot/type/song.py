from bot.type.variable_store import strip_youtube_title

from .error import Error


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
            self.image_url = song.image_url
            self.abr = song.abr
            self.codec = song.codec
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
            self.image_url = None
            self.abr = None
            self.codec = None

    @property
    def image(self):
        if self.image_url is not None and self.image_url != "":
            return self.image_url
        if self.thumbnail is not None and self.thumbnail != "":
            return self.thumbnail
        return None

    @staticmethod
    def from_dict(d):
        song = Song()
        song.title = strip_youtube_title(d["title"])
        song.term = d["term"]
        song.id = d["id"]
        song.link = d["link"]
        song.stream = d["stream"]
        song.duration = d["duration"]
        song.loadtime = d["loadtime"]
        song.thumbnail = d["thumbnail"]
        song.codec = d["codec"]
        return song
