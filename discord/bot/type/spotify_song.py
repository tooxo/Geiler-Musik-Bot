class SpotifySong:
    def __init__(
        self, title: str, image_url: (str, None), artist=None, song_name=None
    ):
        self.title = title
        self.image_url = image_url
        self.artist = artist
        self.song_name = song_name
