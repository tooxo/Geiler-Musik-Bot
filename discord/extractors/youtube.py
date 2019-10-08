from youtube_dl import YoutubeDL
import time
import asyncio
from extractors import mongo
import logging_manager
from multiprocessing import Queue
from expiringdict import ExpiringDict
from bs4 import BeautifulSoup
import aiohttp
from variable_store import strip_youtube_title, Errors
from url_parser import YouTubeType
from song_store import Song, Error
from urllib.parse import quote
import re
import async_timeout

log = logging_manager.LoggingManager()


class YoutubeDLLogger(object):
    def debug(self, msg):
        if "youtube:search" in msg and "query" in msg:
            log.debug(
                logging_manager.debug_info(
                    "[YouTube Search] Searched Term: '"
                    + msg.split('"')[1].split('"')[-1]
                    + "'"
                )
            )

    def warning(self, msg):
        log.warning(logging_manager.debug_info(msg))

    def error(self, msg):
        log.error(logging_manager.debug_info(msg))


class Youtube:
    def __init__(self):
        log.debug("[Startup]: Initializing YouTube Module . . .")
        self.mongo = mongo.Mongo()
        self.queue = Queue()
        self.cache = ExpiringDict(max_age_seconds=10800, max_len=1000)
        self.search_cache = dict()
        self.session = aiohttp.ClientSession()

    async def extract_manifest(self, manifest_url):
        log.debug(
            "[YouTube Extraction] Found a Manifest instead of a video url. Extracting."
        )
        manifest_pattern = re.compile(
            r"<Representation id=\"\d+\" codecs=\"\S+\" audioSamplingRate=\"(\d+)\" startWithSAP=\"\d\" "
            r"bandwidth=\"\d+\">(<AudioChannelConfiguration[^/]+/>)?<BaseURL>(\S+)</BaseURL>"
        )
        with async_timeout.timeout(5):
            async with self.session.get(manifest_url) as res:
                text = await res.text()
                it = re.finditer(manifest_pattern, text)
                return_stream_url = ""
                return_sample_rate = 0
                for match in it:
                    if int(match.group(1)) >= return_sample_rate:
                        return_stream_url = match.group(3)
                        return_sample_rate = int(match.group(1))

                return return_stream_url
        return ""

    async def search_youtube(self, query):
        if query in self.search_cache:
            return self.search_cache[query]
        try:
            log.debug("[YouTube Search] Searched Term: '" + query + "'")
            query = quote(query)
            url = (
                "https://www.youtube.com/results?search_query="
                + query
                + "&sp=EgIQAQ%253D%253D"
            )  # SP = Video only
            url_list = []
            await asyncio.get_event_loop().run_in_executor(None, self.queue.put, query)
            async with self.session.get(url) as res:
                text = await res.text()
                soup = BeautifulSoup(text, "html.parser")
                for vid in soup.findAll(attrs={"class": "yt-uix-tile-link"}):
                    url_list.append(vid["href"])
            self.search_cache[query] = "https://www.youtube.com" + url_list[0]
            for url in url_list:
                if url.startswith("/watch"):
                    return "https://www.youtube.com" + url
        except (IndexError, KeyError) as e:
            e = Error(True)
            e.reason = Errors.no_results_found
            return e
        except (
            aiohttp.ServerTimeoutError,
            aiohttp.ServerDisconnectedError,
            aiohttp.ClientConnectionError,
        ) as e:
            e = Error(True)
            e.reason = Errors.cant_reach_youtube
            return e
        except Exception as er:
            import traceback

            print(traceback.format_exc(er.__traceback__))
            return Error(True)
        return Error(True)

    async def youtube_term(self, term):
        loop = asyncio.get_event_loop()
        url = await self.search_youtube(term)

        if type(url) is Error:
            return url

        youtube = await loop.run_in_executor(None, self.youtube_url_sync, url)

        if type(youtube) is Error:
            return youtube

        if "manifest.googlevideo" in youtube.stream:
            youtube.stream = await self.extract_manifest(youtube.stream)

        asyncio.run_coroutine_threadsafe(
            self.mongo.append_response_time(youtube.loadtime), loop
        )
        youtube.term = term
        return youtube

    def youtube_url_sync(self, url):
        try:
            video = YouTubeType(url)
            if not video.valid:
                e = Error(True)
                e.reason = "Invalid YouTube Url"
                return e
            video_id = video.id
            if self.cache.get(video_id) is not None:
                return self.cache.get(video_id)
            start = time.time()
            self.queue.put(url)
            song = Song()
            with YoutubeDL({"logger": YoutubeDLLogger()}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                song.link = url
                song.id = info_dict["id"]
                song.title = info_dict["title"]
                song.term = url
                for item in info_dict["formats"]:
                    if "audio only" in item["format"]:
                        song.stream = item["url"]
                song.duration = info_dict["duration"]
            song.loadtime = time.time() - start
            for n in info_dict["thumbnails"]:
                song.thumbnail = n["url"]
            song.title = strip_youtube_title(song.title)
            self.cache[song.id] = song
            return song
        except Exception as ex:
            import traceback

            print(traceback.format_exc(ex.__traceback__))
            e = Error(True)
            e.reason = str(ex)
            return e

    async def youtube_url(self, url):
        loop = asyncio.get_event_loop()
        youtube = await loop.run_in_executor(None, self.youtube_url_sync, url)

        if type(youtube) is Error:
            return youtube

        if "manifest.googlevideo" in youtube.stream:
            youtube.stream = await self.extract_manifest(youtube.stream)

        asyncio.run_coroutine_threadsafe(
            self.mongo.append_response_time(youtube.loadtime), loop
        )
        return youtube

    def youtube_playlist_sync(self, url):
        self.queue.put(url)
        youtube_dl_opts = {
            "ignoreerrors": True,
            "extract_flat": True,
            "logger": YoutubeDLLogger(),
        }
        output = []
        with YoutubeDL(youtube_dl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            for video in info_dict["entries"]:
                if not video:
                    continue
                song = Song()
                song.title = video["title"]
                song.link = "https://youtube.com/watch?v=" + video["url"]
                output.append(song)
        return output

    async def youtube_playlist(self, url):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.youtube_playlist_sync, url)
