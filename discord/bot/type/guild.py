from .queue import Queue


class Guild:
    def __init__(self):
        self.voice_client = None
        self.voice_channel = None
        self.song_queue = Queue()
        self.now_playing_message = None
        self.now_playing = None
        self.volume = 0.5
