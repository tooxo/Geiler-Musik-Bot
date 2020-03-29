"""
Song
"""
import json

from bot.type.variable_store import strip_youtube_title


class Song:
    """
    Song
    """

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
        user=None,
        image_url=None,
        abr=None,
        codec=None,
        song_name=None,
        artist=None,
        guild_id=None,
    ) -> None:
        if song:
            self.title = song.title
            self.term = song.term
            self.id = song.id  # pylint: disable=invalid-name
            self.link = song.link
            self.stream = song.stream
            self.duration = song.duration
            self.loadtime = song.loadtime
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
            self.user = user
            self.image_url = image_url
            self.abr = abr
            self.codec = codec

            self.song_name = song_name
            self.artist = artist
            self.guild_id = guild_id

        self.cipher = ""

    @property
    def image(self):
        """
        Return AlbumArt
        @return:
        """
        if self.image_url is not None and self.image_url != "":
            return self.image_url
        if self.thumbnail is not None and self.thumbnail != "":
            return self.thumbnail
        return None

    @staticmethod
    def from_dict(_dict: dict):
        """
        Create a song from a dict
        @param _dict:
        @return:
        """
        song = Song()
        for attribute in _dict.keys():
            if attribute == "title":
                setattr(song, attribute, strip_youtube_title(_dict[attribute]))
            else:
                setattr(song, attribute, _dict.get(attribute, None))
        return song

    @staticmethod
    def copy_song(_from, _to) -> "Song":
        """
        Copy contents from one song object to another
        @param _from:
        @param _to:
        @return:
        """
        _from: Song
        _to: Song
        for attribute in _from.__dict__.keys():
            if hasattr(_from, attribute) and attribute != "image_url":
                if getattr(_from, attribute) is not None:
                    setattr(_to, attribute, getattr(_from, attribute))
        return _to

    def __str__(self):
        _temp_dict = {}
        for attr in self.__dict__:
            if type(  # pylint: disable=unidiomatic-typecheck
                self.__dict__.get(attr)
            ) in (str, int, list, None):
                _temp_dict[attr] = self.__dict__.get(attr)
        return json.dumps(_temp_dict)
