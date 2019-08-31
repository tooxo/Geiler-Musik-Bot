from youtube_dl import YoutubeDL
import time
import asyncio
import mongo
import logging_manager
import re
from multiprocessing import Queue
from expiringdict import ExpiringDict
from bs4 import BeautifulSoup
import aiohttp
from variable_store import VariableStore, strip_youtube_title

log = logging_manager.LoggingManager()


class YoutubeDLLogger(object):
    def debug(self, msg):
        if "youtube:search" in msg and "query" in msg:
            log.debug(
                logging_manager.debug_info("[YouTube Search] Searched Term: '" + msg.split('"')[1].split('"')[-1] + "'")
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

    async def search_youtube(self, query):
        if query in self.search_cache:
            return self.search_cache[query]
        try:
            log.debug("[YouTube Search] Searched Term: '" + query + "'")
            url = "https://www.youtube.com/results?search_query=" + query + "&sp=EgIQAQ%253D%253D"  # SP = Video only
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
            return "NO RESULTS FOUND"

    async def youtube_term(self, term):
        loop = asyncio.get_event_loop()
        url = await self.search_youtube(term)
        if url is "NO RESULTS FOUND":
            return {"error": True, "reason": "No results found."}
        youtube = await loop.run_in_executor(None, self.youtube_url_sync, url)
        if youtube["error"] is False:
            asyncio.run_coroutine_threadsafe(self.mongo.append_response_time(youtube["loadtime"]), loop)
        return youtube

    def youtube_url_sync(self, url):
        try:
            video_id = re.search(VariableStore.youtube_verify_pattern, url).group(1)
            if self.cache.get(video_id) is not None:
                return self.cache.get(video_id)
            start = time.time()
            self.queue.put(url)
            dictionary = dict()
            with YoutubeDL({"logger": YoutubeDLLogger()}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                dictionary["link"] = url
                dictionary["id"] = info_dict["id"]
                dictionary["title"] = info_dict["title"]
                dictionary["term"] = url
                for item in info_dict["formats"]:
                    if "audio only" in item["format"]:
                        dictionary["stream"] = item["url"]
                dictionary["duration"] = info_dict["duration"]
            dictionary["loadtime"] = time.time() - start
            if "manifest.googlevideo.com" in dictionary["stream"]:
                return {"error": True, "reason": "Malformed Stream. Trying again.", "link": url}
            else:
                dictionary["error"] = False
            dictionary["title"] = strip_youtube_title(dictionary["title"])
            self.cache[dictionary["id"]] = dictionary
            return dictionary
        except Exception as e:
            return {"error": True, "reason": str(e)}

    async def youtube_url(self, url):
        loop = asyncio.get_event_loop()
        youtube = await loop.run_in_executor(None, self.youtube_url_sync, url)
        asyncio.run_coroutine_threadsafe(self.mongo.append_response_time(youtube["loadtime"]), loop)
        return youtube

    def youtube_playlist_sync(self, url):
        self.queue.put(url)
        youtube_dl_opts = {"ignoreerrors": True, "extract_flat": True, "logger": YoutubeDLLogger()}
        output = []
        with YoutubeDL(youtube_dl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            for video in info_dict["entries"]:
                if not video:
                    continue
                dic = dict()
                dic["title"] = video["title"]
                dic["link"] = "https://youtube.com/watch?v=" + video["url"]
                output.append(dic)
        return output

    async def youtube_playlist(self, url):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.youtube_playlist_sync, url)
