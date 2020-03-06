import os
import time

import motor.motor_asyncio

import logging_manager


class Mongo:
    def __init__(self):
        self.log = logging_manager.LoggingManager()
        self.log.debug("[Startup]: Initializing Mongo Module . . .")
        self.mongo_enabled = os.environ.get("MONGO_ENABLED", "True") == "True"
        self.log.debug("[Startup]: Mongo is " + str(self.mongo_enabled))
        if self.mongo_enabled:
            self.host = os.environ.get("MONGODB_URI", "")

            self.client: motor.motor_asyncio.AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(
                self.host
            )
            self.db = self.client.get_database(
                os.environ.get("MONGODB_DATABASE_NAME", "discordbot")
            )

            self.connection_time_collection = self.db.connectiontime
            self.most_played_collection = self.db.most_played_collection

    async def append_response_time(self, response_time):
        if self.mongo_enabled is False:
            return
        current_time = time.time()
        every = self.connection_time_collection.find()
        async for item in every:
            if item["x"] < current_time * 1000 - 86400000:
                await self.connection_time_collection.delete_one(
                    {"_id": item["_id"]}
                )
        obj = {"x": int(time.time()) * 1000, "y": response_time * 10}
        await self.connection_time_collection.insert_one(obj)

    async def append_most_played(self, song_name):
        if self.mongo_enabled is False:
            return
        song_name = song_name.replace('"', "")
        song_name = song_name.replace("'", "")
        song = await self.most_played_collection.find_one({"name": song_name})
        if song is not None:
            await self.most_played_collection.update_one(
                {"_id": song["_id"]}, {"$inc": {"val": 1}}
            )
        else:
            obj = {"name": song_name, "val": 1}
            await self.most_played_collection.insert_one(obj)

    @staticmethod
    async def insert_empty(
        collection,
        guild_id,
        volume="0.5",
        full="█",
        empty="░",
        service="basic",
        announce=True,
    ):
        await collection.insert_one(
            {
                "id": guild_id,
                "volume": volume,
                "full": full,
                "empty": empty,
                "service": service,
                "announce": announce,
            }
        )

    async def set_volume(self, guild_id, volume):
        if self.mongo_enabled is False:
            return
        collection = self.db.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            await self.insert_empty(
                collection=collection, guild_id=guild_id, volume=volume
            )
        else:
            await collection.update_one(
                {"id": guild_id}, {"$set": {"volume": volume}}
            )

    async def get_volume(self, guild_id):
        if self.mongo_enabled is False:
            return 0.5
        collection = self.db.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            return 0.5
        return doc["volume"]

    async def set_chars(self, guild_id, full, empty):
        if self.mongo_enabled is False:
            return
        collection = self.db.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            await self.insert_empty(
                collection, guild_id, full=full, empty=empty
            )
        else:
            await collection.update_one(
                {"id": guild_id}, {"$set": {"full": full, "empty": empty}}
            )

    async def get_chars(self, guild_id):
        if self.mongo_enabled is False:
            return "█", "░"
        collection = self.db.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            return "█", "░"
        return doc["full"], doc["empty"]

    async def set_service(self, guild_id, service):
        if self.mongo_enabled is False:
            return
        collection = self.db.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            await self.insert_empty(collection, guild_id, service=service)
        else:
            await collection.update_one(
                {"id": guild_id}, {"$set": {"service": service}}
            )

    async def get_service(self, guild_id):
        if self.mongo_enabled is False:
            return "basic"
        collection = self.db.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            return "basic"
        return doc["service"]

    async def set_announce(self, guild_id, announce_status):
        if self.mongo_enabled is False:
            return
        collection = self.db.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            await self.insert_empty(
                collection, guild_id, announce=announce_status
            )
        else:
            await collection.update_one(
                {"id": guild_id}, {"$set": {"announce": announce_status}}
            )

    async def get_announce(self, guild_id) -> bool:
        if self.mongo_enabled is False:
            return True
        collection = self.db.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            return True
        return doc["announce"]

    async def set_restart_key(self, restart_key):
        if self.mongo_enabled is False:
            return
        collection = self.db.secure
        x = await collection.find_one({"type": "restart_code"})
        if x is None:
            await collection.insert_one(
                {"type": "restart_code", "code": restart_key}
            )
        else:
            await collection.update_one(
                {"type": "restart_code"}, {"$set": {"code": restart_key}}
            )

    async def get_restart_key(self):
        if self.mongo_enabled is False:
            return
        collection = self.db.secure
        x = await collection.find_one({"type": "restart_code"})
        return x["code"]
