import asyncio
import os

import aiohttp
import async_timeout

import logging_manager


class LastFM:
    def __init__(self):
        self.api_key = os.environ.get("LASTFM_KEY", "")
        self.session = aiohttp.ClientSession()
        self.cache = dict()

    async def get_album_art(self, youtube_title, searched_term):

        if youtube_title in self.cache:
            return self.cache[youtube_title]
        if searched_term in self.cache:
            return self.cache[searched_term]

        try:
            search_url = (
                "http://ws.audioscrobbler.com/2.0/?method=track.search&track="
                + youtube_title
                + "&api_key="
                + self.api_key
                + "&format=json"
            )

            print("SEARCHING COVER")

            with async_timeout.timeout(5):
                async with self.session.get(search_url) as response:
                    json = await response.json()

            title = json["results"]["trackmatches"]["track"][0]["name"]
            artist = json["results"]["trackmatches"]["track"][0]["artist"]

            art_url = (
                "http://ws.audioscrobbler.com/2.0/?method=track.getinfo&api_key="
                + self.api_key
                + "&artist="
                + artist
                + "&track="
                + title
                + "&format=json"
            )

            with async_timeout.timeout(5):
                async with self.session.get(art_url) as response:
                    art_json = await response.json()

            image_url = art_json["track"]["album"]["image"][2]["#text"]
            self.cache[youtube_title] = image_url
            self.cache[searched_term] = image_url
            return image_url
        except (
            KeyError,
            TypeError,
            aiohttp.ServerTimeoutError,
            NameError,
            IndexError,
            TimeoutError,
            asyncio.TimeoutError,
        ):
            try:
                search_url = (
                    "http://ws.audioscrobbler.com/2.0/?method=track.search&track="
                    + searched_term
                    + "&api_key="
                    + self.api_key
                    + "&format=json"
                )

                with async_timeout.timeout(3):
                    async with self.session.get(search_url) as response:
                        json = await response.json()

                title = json["results"]["trackmatches"]["track"][0]["name"]
                artist = json["results"]["trackmatches"]["track"][0]["artist"]

                art_url = (
                    "http://ws.audioscrobbler.com/2.0/?method=track.getinfo&api_key="
                    + self.api_key
                    + "&artist="
                    + artist
                    + "&track="
                    + title
                    + "&format=json"
                )

                with async_timeout.timeout(3):
                    async with self.session.get(art_url) as response:
                        art_json = await response.json()

                image_url = art_json["track"]["album"]["image"][2]["#text"]
                self.cache[searched_term] = image_url
                return image_url
            except (
                KeyError,
                TypeError,
                aiohttp.ServerTimeoutError,
                NameError,
                IndexError,
                TimeoutError,
                asyncio.TimeoutError,
            ):
                return None
