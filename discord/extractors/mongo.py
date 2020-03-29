"""
Mongo
"""
import os
import time

from typing import Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorClient

import logging_manager


class Mongo:
    """
    Mongo
    """

    def __init__(self) -> None:
        self.log = logging_manager.LoggingManager()
        self.log.debug("[Startup]: Initializing Mongo Module . . .")
        self.mongo_enabled = os.environ.get("MONGO_ENABLED", "True") == "True"
        self.log.debug("[Startup]: Mongo is " + str(self.mongo_enabled))
        if self.mongo_enabled:
            self.host = os.environ.get("MONGODB_URI", "")

            self.client: AsyncIOMotorClient = AsyncIOMotorClient(self.host)
            self.database = self.client.get_database(
                os.environ.get("MONGODB_DATABASE_NAME", "discordbot")
            )

            self.connection_time_collection = self.database.connectiontime
            self.most_played_collection = self.database.most_played_collection

    async def append_response_time(self, response_time: int) -> None:
        """
        Append Response Time to Mongo
        @param response_time:
        @return:
        """
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

    async def append_most_played(self, song_name: str) -> None:
        """
        Append Most Played to Mongo
        @param song_name:
        @return:
        """
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
    ) -> None:
        """
        Insert an empty entry for a guild
        @param collection:
        @param guild_id:
        @param volume:
        @param full:
        @param empty:
        @param service:
        @param announce:
        @return:
        """
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

    async def set_volume(self, guild_id: str, volume: str) -> None:
        """
        Set the volume to Mongo
        @param guild_id:
        @param volume:
        @return:
        """
        if self.mongo_enabled is False:
            return
        collection = self.database.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            await self.insert_empty(
                collection=collection, guild_id=guild_id, volume=volume
            )
        else:
            await collection.update_one(
                {"id": guild_id}, {"$set": {"volume": volume}}
            )

    async def get_volume(self, guild_id) -> float:
        """
        Get Volume from Mongo
        @param guild_id:
        @return:
        """
        if self.mongo_enabled is False:
            return 0.5
        collection = self.database.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            return 0.5
        return doc["volume"]

    async def set_chars(self, guild_id: str, full: str, empty: str) -> None:
        """
        Set chars to Mongo
        @param guild_id:
        @param full:
        @param empty:
        @return:
        """
        if self.mongo_enabled is False:
            return
        collection = self.database.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            await self.insert_empty(
                collection, guild_id, full=full, empty=empty
            )
        else:
            await collection.update_one(
                {"id": guild_id}, {"$set": {"full": full, "empty": empty}}
            )

    async def get_chars(self, guild_id) -> Tuple[str, str]:
        """
        Get Chars from Mongo
        @param guild_id:
        @return:
        """
        if self.mongo_enabled is False:
            return "█", "░"
        collection = self.database.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            return "█", "░"
        return doc["full"], doc["empty"]

    async def set_service(self, guild_id: str, service: str) -> None:
        """
        Set service name to mongo
        @param guild_id:
        @param service:
        @return:
        """
        if self.mongo_enabled is False:
            return
        collection = self.database.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            await self.insert_empty(collection, guild_id, service=service)
        else:
            await collection.update_one(
                {"id": guild_id}, {"$set": {"service": service}}
            )

    async def get_service(self, guild_id: str) -> str:
        """
        Get service name from mongo
        @param guild_id:
        @return:
        """
        if self.mongo_enabled is False:
            return "basic"
        collection = self.database.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            return "basic"
        return doc["service"]

    async def set_announce(self, guild_id: str, announce_status: bool) -> None:
        """
        Set announce state
        @param guild_id:
        @param announce_status:
        @return:
        """
        if self.mongo_enabled is False:
            return
        collection = self.database.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            await self.insert_empty(
                collection, guild_id, announce=announce_status
            )
        else:
            await collection.update_one(
                {"id": guild_id}, {"$set": {"announce": announce_status}}
            )

    async def get_announce(self, guild_id: str) -> bool:
        """
        Get announce state from mongo
        @param guild_id:
        @return:
        """
        if self.mongo_enabled is False:
            return True
        collection = self.database.guilds
        doc = await collection.find_one({"id": guild_id})
        if doc is None:
            return True
        return doc["announce"]

    async def set_restart_key(self, restart_key: str) -> None:
        """
        Set the restart key to mongo
        @param restart_key:
        @return:
        """
        if self.mongo_enabled is False:
            return
        collection = self.database.secure
        entry = await collection.find_one({"type": "restart_code"})
        if entry is None:
            await collection.insert_one(
                {"type": "restart_code", "code": restart_key}
            )
        else:
            await collection.update_one(
                {"type": "restart_code"}, {"$set": {"code": restart_key}}
            )

    async def get_restart_key(self) -> Optional[str]:
        """
        Get the restart key from mongo
        @return:
        """
        if self.mongo_enabled is False:
            return
        collection = self.database.secure
        entry = await collection.find_one({"type": "restart_code"})
        return entry["code"]
