from .queue import Queue


class Guild:
    def __init__(self):
        self.voice_client = None
        self.voice_channel = None
        self.song_queue = Queue()
        self.now_playing_message = None
        self.now_playing = None
        self.volume = 0.5
        self.full = "█"
        self.empty = "░"

        self.search_service = "basic"

    async def inflate_from_mongo(self, mongo, guild_id):
        self.volume = await mongo.get_volume(guild_id)
        self.full, self.empty = await mongo.get_chars(guild_id)
        self.search_service = await mongo.get_service(guild_id)

    @property
    def service(self):
        return self.search_service
