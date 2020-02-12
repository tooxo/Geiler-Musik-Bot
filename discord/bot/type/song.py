import json

from bot.type.variable_store import strip_youtube_title

from .error import Error


class Song:
    def __init__(
        self,
        song=None,
        title=None,
        term=None,
        _id=None,
        link=None,
        stream=None,
        duration=None,
        loadtime=None,
        thumbnail=None,
        error=Error(False),
        user=None,
        image_url=None,
        abr=None,
        codec=None,
        song_name=None,
        artist=None,
        guild_id=None,
    ):
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

            self.song_name = song.song_name
            self.artist = song.artist
            self.guild_id = song.guild_id
        else:
            self.title = title
            self.term = term
            self.id = _id
            self.link = link
            self.stream = stream
            self.duration = duration
            self.loadtime = loadtime
            self.thumbnail = thumbnail
            self.error = error
            self.user = user
            self.image_url = image_url
            self.abr = abr
            self.codec = codec

            self.song_name = song_name
            self.artist = artist
            self.guild_id = guild_id

        self.cipher = ""
        self.youtube_stream = None

    @property
    def image(self):
        if self.image_url is not None and self.image_url != "":
            return self.image_url
        if self.thumbnail is not None and self.thumbnail != "":
            return self.thumbnail
        return None

    @staticmethod
    def from_dict(d: dict):
        song = Song()
        for a in d.keys():
            if a == "title":
                setattr(song, a, strip_youtube_title(d[a]))
            else:
                setattr(song, a, d.get(a, None))
        return song

    @staticmethod
    def copy_song(_from, _to):
        _from: Song
        _to: Song
        for attribute in _from.__dict__.keys():
            if hasattr(_from, attribute) and attribute != "image_url":
                if getattr(_from, attribute) is not None:
                    setattr(_to, attribute, getattr(_from, attribute))
        return _to

    def to_string(self):
        x = {}
        for attr in self.__dict__:
            if type(self.__dict__.get(attr)) in (str, int, list, None):
                x[attr] = self.__dict__.get(attr)
        return json.dumps(x)
