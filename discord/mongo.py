import time
import os
import motor.motor_asyncio


class Mongo:
    def __init__(self):
        print("[Startup]: Initializing Mongo Module . . .")
        try:
            self.host = os.environ['MONGODB_URI']
        except Exception:
            self.host = ""
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.host)
        try:
            self.db = eval("self.client." + os.environ['MONGODB_USER'])
        except:
            self.db = ""
        self.collection = self.db.connectiontime
        self.most_played_collection = self.db.most_played_collection

        alternative_host = 'mongodb://database:27017'
        alternative_client = motor.motor_asyncio.AsyncIOMotorClient(alternative_host)
        self.alternative_db = alternative_client.discordbot

    async def appendResponsetime(self, responsetime):
        current_time = time.time()
        all = self.collection.find()
        async for item in all:
            if item['x'] < current_time * 1000 - 86400000:
                await self.collection.delete_one({'_id': item['_id']})
        obj = {'x': int(time.time()) * 1000, 'y': responsetime * 10}
        await self.collection.insert_one(obj)

    async def appendMostPlayed(self, songname):
        songname = songname.replace('"', "")
        songname = songname.replace("'", "")
        song = await self.most_played_collection.find_one({"name": songname})
        if song is not None:
            await self.most_played_collection.update_one({'_id': song['_id']}, {'$inc': {'val': 1}})
        else:
            obj = {'name': songname, 'val': 1}
            await self.most_played_collection.insert_one(obj)

    async def set_volume(self, guild_id, volume):
        collection = self.alternative_db.volume
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            await collection.insert_one({'id': guild_id, 'volume': volume})
        else:
            await collection.update_one({'id': guild_id}, {'$set': {'volume': volume}})

    async def get_volume(self, guild_id):
        collection = self.alternative_db.volume
        doc = await collection.find_one({'id': guild_id})
        if doc is None:
            return 0.5
        else:
            return doc['volume']

    async def set_chars(self, guild_id, full, empty):
        collection = self.alternative_db.chars
        doc = await collection.find_one({'id': guild_id})
        if doc is None:
            await collection.insert_one({'id': guild_id, 'full': full, 'empty': empty})
        else:
            await collection.update_one({'id': guild_id}, {'$set': {'full': full, 'empty': empty}})

    async def get_chars(self, guild_id):
        collection = self.alternative_db.chars
        doc = await collection.find_one({'id': guild_id})
        if doc is None:
            return '█', '░'
        else:
            return doc['full'], doc['empty']
