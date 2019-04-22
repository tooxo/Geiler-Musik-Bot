import json as JSON
import time
import os
import asyncio
import motor.motor_asyncio

class Mongo():
    def __init__(self):
        print("[Startup]: Initializing Mongo Module . . .")
        self.host = os.environ['MONGODB_URI']
        self.client = motor.motor_asyncio.AsyncIOMotorClient(self.host)
        self.db = eval("self.client."+os.environ['MONGODB_USER'])
        self.collection = self.db.connectiontime
        self.mostcollection = self.db.mostcollection

    async def appendResponsetime(self, responsetime):
        current_time = time.time()
        all = self.collection.find()
        for item in all:
            if item['x'] < current_time - 60480000:
                await self.collection.delete_one({'_id': item['_id']})
        obj = {'x': int(time.time()) * 1000, 'y': resp * 10}
        await self.collection.insert_one(obj)

    async def appendMostPlayed(self, songname):
        songname = songname.replace('"', "")
        songname = songname.replace("'", "")
        song = await self.mostcollection.find_one({"name": songname})
        if song is not None:
            await self.mostcollection.update_one({'_id': song['_id']}, {'$inc': {'val': 1}})
        else:
            obj = {'name': songname, 'val': 1}
            await self.mostcollection.insert_one(obj)
