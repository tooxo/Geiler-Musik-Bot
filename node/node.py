"""
Node
"""
import asyncio
import http.client
import json
import os
import random
import re
import time
import traceback
import urllib.request
from http.client import HTTPResponse
from typing import List, Tuple, Union
from urllib.parse import quote

from expiringdict import ExpiringDict
from karp.client import KARPClient
from karp.request import Request
from yaml import YAMLError, safe_load
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError, ExtractorError

from discord_handler import DiscordHandler


class Errors:
    """
    All Errors
    """

    no_results_found = "No Results found."
    default = "An Error has occurred."
    info_check = "An Error has occurred while checking Info."
    spotify_pull = (
        "**There was an error pulling the Playlist, 0 Songs were added. "
        "This may be caused by the playlist being private or deleted.**"
    )
    cant_reach_youtube = (
        "Can't reach YouTube. Server Error on their side maybe?"
    )
    youtube_url_invalid = "This YouTube Url is invalid."
    youtube_video_not_available = (
        "The requested YouTube Video is not available."
    )
    error_please_retry = "error_please_retry"
    backend_down = (
        "Our backend seems to be down right now, try again in a few minutes."
    )


class YoutubeDLLogger(object):
    """
    Custom logger for YoutubeDL
    """

    @staticmethod
    def debug(msg: str) -> None:
        """
        Print debug
        :param msg: message
        :return:
        """
        if "youtube:search" in msg and "query" in msg:
            print(
                "[YouTube Search] Searched Term: '"
                + msg.split('"')[1].split('"')[-1]
                + "'"
            )

    @staticmethod
    def warning(msg: str) -> None:
        """
        Print warning
        :param msg: message
        :return:
        """
        print("warn", msg)

    @staticmethod
    def error(msg: str) -> None:
        """
        Print error
        :param msg: message
        :return:
        """
        if "This video is no longer available" in msg:
            raise NotAvailableException("notavailable")
        raise ExtractorError("Video Downloading failed.")


class NotAvailableException(Exception):
    """
    Exception raised if a video is unavailable
    """

    pass


class YouTube:
    """
    Class to interact with YouTube
    """

    def __init__(self) -> None:
        self.research_cache: ExpiringDict = ExpiringDict(1000, 10000)
        self.search_cache: dict = dict()
        self.music_search_cache: dict = dict()
        self.logger = YoutubeDLLogger()

    @staticmethod
    def extract_manifest(manifest_url: str) -> str:
        """
        Extract a stream url from a manifest url
        :param manifest_url:
        :return:
        """
        manifest_pattern = re.compile(
            r"<Representation id=\"\d+\" codecs=\"\S+\" audioSamplingRate=\"(\d+)\" startWithSAP=\"\d\" "
            r"bandwidth=\"\d+\">(<AudioChannelConfiguration[^/]+/>)?<BaseURL>(\S+)</BaseURL>"
        )
        print("extracting from manifest:", manifest_url)
        with urllib.request.urlopen(manifest_url) as res:
            text = res.read().decode()
            it = re.finditer(manifest_pattern, text)
            return_stream_url = ""
            return_sample_rate = 0
            for match in it:
                if int(match.group(1)) >= return_sample_rate:
                    return_stream_url = match.group(3)
                    return_sample_rate = int(match.group(1))
            return return_stream_url

    @staticmethod
    def get_format(formats: List[dict]) -> Tuple[str, str, int]:
        """
        Decide on a format from all formats
        :param formats: formats
        :return:
        """
        for item in formats:
            if item["format_id"] == "250":
                return item["url"], item["acodec"], item["abr"]
        for item in formats:
            if item["format_id"] == "251":
                return item["url"], item["acodec"], item["abr"]
        for item in formats:
            if item["format_id"] == "249":
                return item["url"], item["acodec"], item["abr"]
        for item in formats:
            # return some audio stream
            if "audio only" in item["format"]:
                return item["url"], item["acodec"], item["abr"]

    def youtube_extraction(self, video_id: str, url: str) -> Union[dict, str]:
        """
        Extract data from YouTube
        :param video_id:
        :param url:
        :return:
        """
        try:
            start = time.time()
            if self.research_cache.get(video_id, None) is not None:
                return self.research_cache.get(video_id)
            with YoutubeDL({"logger": self.logger}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                song = {
                    "link": url,
                    "id": info_dict["id"],
                    "title": info_dict["title"],
                }
                yt_s, c, abr = self.get_format(info_dict["formats"])
                song["stream"] = yt_s
                song["codec"] = c
                song["abr"] = abr
                # preferring format 250: 78k bitrate (discord default = 64, max = 96) + already opus formatted

                if "manifest" in song["stream"]:
                    # youtube-dl doesn't handle manifest extraction, so I need to do it.
                    song["stream"] = self.extract_manifest(song["stream"])
                song["duration"] = info_dict["duration"]
            for n in info_dict["thumbnails"]:
                song["thumbnail"] = n["url"]
            song["term"] = ""
            song["loadtime"] = int(time.time() - start)
            self.research_cache[song["id"]] = song
            del info_dict
            return song
        except NotAvailableException:
            return Errors.youtube_video_not_available
        except (DownloadError, ExtractorError):
            traceback.print_exc()
            return Errors.default
        except Exception as ex:
            print(ex)
            return Errors.error_please_retry

    def extract_playlist(self, playlist_id: str) -> List[dict]:
        """
        Extract tracks from playlist url
        :param playlist_id: playlist id
        :return:
        """
        url = "https://youtube.com/playlist?list=" + playlist_id
        youtube_dl_opts = {
            "extract_flat": True,
            "ignore_errors": True,
            "logger": self.logger,
        }
        output = []
        with YoutubeDL(youtube_dl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            for video in info_dict["entries"]:
                if not video:
                    continue
                song = dict()
                song["title"] = video["title"]
                song["link"] = "https://youtube.com/watch?v=" + video["url"]
                output.append(song)
            del info_dict
        return output

    def search_youtube_basic(self, term: str) -> str:
        """
        Search YouTube
        :param term:
        :return:
        """
        if term in self.search_cache:
            return self.search_cache[term]
        query = quote(term)
        url = f"https://www.youtube.com/results?search_query={query}%2C+video&pbj=1"
        for x in range(0, 2, 1):
            url_list = []
            request = urllib.request.Request(
                url,
                headers={
                    "x-youtube-client-name": "1",
                    "x-youtube-client-version": "2.20200312.05.00",
                },
            )
            with urllib.request.urlopen(request) as res:
                res: HTTPResponse
                if res.status != 200:
                    continue
                text = res.read()
                data = json.loads(text)

                data = data[1]["response"]["contents"][
                    "twoColumnSearchResultsRenderer"
                ]["primaryContents"]["sectionListRenderer"]["contents"]

                for item in data:
                    for sub in item["itemSectionRenderer"]["contents"]:
                        if "videoRenderer" in sub:
                            url_list.append(sub["videoRenderer"]["videoId"])
                if len(url_list) > 0:
                    return f"https://youtube.com/watch?v={url_list[0]}"

        raise NotAvailableException(Errors.no_results_found)

    @staticmethod
    def _create_music_payload(query: str):
        payload: dict = {
            "context": {
                "client": {
                    "clientName": "WEB_REMIX",
                    "clientVersion": "0.1",
                    "hl": "en",
                    "gl": "US",
                },
                "user": {"enableSafetyMode": False},
            },
            "query": query,
        }
        return json.dumps(payload)

    @staticmethod
    def _get_stream_from_youtube_music_response(input_json: dict):
        try:
            video_ids = []
            for renderer in input_json["contents"]["sectionListRenderer"][
                "contents"
            ]:
                try:
                    for chapter in renderer["musicShelfRenderer"]["contents"]:
                        try:
                            video_id = chapter[
                                "musicResponsiveListItemRenderer"
                            ]["overlay"]["musicItemThumbnailOverlayRenderer"][
                                "content"
                            ][
                                "musicPlayButtonRenderer"
                            ][
                                "playNavigationEndpoint"
                            ][
                                "watchEndpoint"
                            ][
                                "videoId"
                            ]
                            video_ids.append(video_id)
                        except (TypeError, KeyError):
                            continue
                except (TypeError, KeyError):
                    continue
            if len(video_ids) > 0:
                return video_ids[0]
            raise NotAvailableException("no videos found")
        except (TypeError, KeyError, AttributeError):
            raise NotAvailableException("no videos found")

    def search_youtube_music(self, term: str) -> str:
        """
        Search YouTube Music
        :param term: Search Term
        :return: YouTube url
        """
        if term in self.music_search_cache:
            return self.music_search_cache[term]
        url = "https://music.youtube.com/youtubei/v1/search?alt=json&key=AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30"
        for x in range(1, 2, 1):
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/80.0.3987.87 Safari/537.36",
                    "Referer": f"https://music.youtube.com/search?q={quote(term)}",
                    "Content-Type": "application/json",
                },
                data=self._create_music_payload(query=term).encode(),
            )
            with urllib.request.urlopen(req) as res:
                res: HTTPResponse
                if res.status != 200:
                    continue
                response: dict = json.loads(res.read())
                video_id = self._get_stream_from_youtube_music_response(
                    response
                )
                self.search_cache[term] = (
                    "https://www.youtube.com"
                    + f"https://youtube.com/watch?v={video_id}"
                )
                return f"https://youtube.com/watch?v={video_id}"

    def search(self, input_json: str) -> str:
        """
        Search
        :param input_json: data
        :return: Search result url
        """
        input_json = json.loads(input_json)
        if input_json.get("service", "basic") == "music":
            return self.search_youtube_music(input_json["term"])
        return self.search_youtube_basic(input_json["term"])


class SoundCloud:
    """
    Class to interact with SoundCloud
    """

    def __init__(self) -> None:
        self.cache: ExpiringDict = ExpiringDict(1000, 10000)
        self.api_key = ""

    API_KEYS = ["a3dd183a357fcff9a6943c0d65664087"]
    URL_RESOLVE = "https://api.soundcloud.com/resolve?url={}&client_id={}"
    URL_STREAM = "https://api.soundcloud.com/i1/tracks/{}/streams?client_id={}"

    SCRIPT_REGEX = re.compile(
        r"(https://a-v2\.sndcdn\.com/assets/48-[\da-z]{8}-[\da-z].js)"
    )

    ID_REGEX = re.compile(r'client_id:"([a-zA-Z0-9]+)"')

    COMMON_HEADERS = {
        "Host": "api-v2.soundcloud.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/70.0.3538.27 Safari/537.36",
        "Accept-Charset": "utf-8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-us,en;q=0.5",
        "Connection": "close",
    }

    PLAYLIST_PATTERN = re.compile(
        r"https://[a-z-\\]+\.sndcdn.com/media/[\d]+/[\d]+[\S]+"
    )

    def _get_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        with urllib.request.urlopen(url="https://soundcloud.com") as res:
            response = res.read().decode()
        script = re.findall(self.SCRIPT_REGEX, response)[0]
        with urllib.request.urlopen(url=script) as res:
            script_src = res.read().decode()
        client_id = re.findall(self.ID_REGEX, script_src)[0]
        self.api_key = client_id
        return client_id

    @staticmethod
    def _decide_on_format(formats: dict):
        for f in formats.keys():
            if "opus" in f:
                f: str
                return formats[f], f.split("_")[1], f.split("_")[2]
        return (
            formats[0],
            list(formats.keys())[0].split("_")[1],
            list(formats.keys())[0].split("_")[2],
        )

    def research_track(self, url: str) -> Union[dict, str]:
        """
        Extract information from an SoundCloud Track
        :param url: soundcloud url
        :return: search result
        """
        if url in self.cache:
            return self.cache.get(url, {})
        try:
            _time = time.time()
            with urllib.request.urlopen(
                url=urllib.request.Request(
                    self.URL_RESOLVE.format(url, self._get_api_key()),
                    headers=self.COMMON_HEADERS,
                )
            ) as res:
                data = json.loads(res.read().decode())

            codec_url = ""
            codec = ""
            abr = 70

            for transcoding in data["media"]["transcodings"]:
                if "opus" in transcoding["preset"]:
                    codec_url = transcoding["url"]
                    codec = "opus"

            if not codec_url:
                codec_url = data["media"]["transcodings"][0]["url"]
                codec = "mp3"

            with urllib.request.urlopen(
                url=urllib.request.Request(
                    f"{codec_url}?client_id={self._get_api_key()}",
                    headers=self.COMMON_HEADERS,
                )
            ) as res:
                url = json.loads(res.read())["url"]

            # with urllib.request.urlopen(
            #    url=urllib.request.Request(
            #        self.URL_STREAM.format(data["id"], self._get_api_key()),
            #        headers=self.COMMON_HEADERS,
            #    )
            # ) as res:
            #    streams = json.loads(res.read().decode())

            # url, codec, abr = self._decide_on_format(streams)

            if "playlist.m3u8" in url:
                with urllib.request.urlopen(url) as res:
                    last_entry = re.findall(
                        self.PLAYLIST_PATTERN, res.read().decode()
                    )[-1]
                    url = re.sub(r"/[\d]+/", "/0/", last_entry)

            song = {
                "title": data.get("title", "_"),
                "link": data.get("permalink_url", ""),
                "duration": round(data.get("duration", 0) / 1000),
                "thumbnail": data.get("artwork_url", ""),
                "loadtime": time.time() - _time,
                "term": data.get("title", "_"),
                "stream": url,
                "codec": codec,
                "abr": abr,
            }

            self.cache[url] = song
            return song
        except (json.JSONDecodeError, KeyError, AttributeError, ValueError):
            traceback.print_exc()
            return Errors.default

    def playlist(self, url: str) -> Union[List[dict], str]:
        """
        Extract songs from SoundCloud playlist
        :param url: playlist url
        :return: songs
        """
        try:
            request = urllib.request.Request(
                url=self.URL_RESOLVE.format(url, self._get_api_key()),
                headers=self.COMMON_HEADERS,
            )
            with urllib.request.urlopen(request) as res:
                res: http.client.HTTPResponse
                data = json.loads(res.read())

            tracks = []
            for track in data["tracks"]:
                tracks.append(
                    {"title": track["title"], "link": track["permalink_url"]}
                )
            return tracks
        except (KeyError, AttributeError, TimeoutError, UnicodeDecodeError):
            traceback.print_exc()
            return Errors.default


class Node:
    def __init__(self):
        # loading config
        if os.path.exists("configuration.yaml"):
            filename = "configuration.yaml"
        elif os.path.exists("./configuration.yml"):
            filename = "./configuration.yml"
        else:
            print("Configuration File Missing.")
            exit(1)
            return
        f = open(filename, "r")
        y = None
        try:
            y = safe_load(f)
        except YAMLError as ex:
            print(ex)
            exit(1)

        self.parent_host = y.get("parent_host", "")
        self.parent_port = y.get("parent_port", "")

        self.api_key = y.get("API_KEY", "API_KEY")

        self.youtube = YouTube()
        self.soundcloud = SoundCloud()
        self.discord = None

        self.client = KARPClient(self.parent_host, self.parent_port)

    async def login(self) -> None:
        """
        Login to the NodeController
        :return:
        """
        self._add_authentication_routes()
        await self.client.open()

    def _add_authentication_routes(self) -> None:
        """
        Add the routes used for authentication.
        :return:
        """

        @self.client.add_route(route="identify")
        def _identify(request: Request):
            return json.dumps({"API_KEY": self.api_key})

        @self.client.add_route(route="accepted")
        async def _accepted(request: Request):
            data = json.loads(request.text)
            self.discord = DiscordHandler(
                data["DISCORD_API_KEY"], self.client, self
            )
            asyncio.ensure_future(self.discord.start())
            await self.discord.started.wait()

            self._add_discord_routes()
            self._add_youtube_routes()
            self._add_soundcloud_routes()

            return "1"

    def _add_youtube_routes(self) -> None:
        """
        Add the routes used for authentication.
        :return:
        """

        @self.client.add_route(route="youtube_video")
        def _youtube_video(request: Request):
            video_id = request.text
            if video_id == "":
                raise Exception("No VideoID provided")
            extracted_content: dict = self.youtube.youtube_extraction(
                video_id=video_id,
                url="https://www.youtube.com/watch?v=" + video_id,
            )
            if isinstance(extracted_content, str):
                raise Exception(extracted_content)
            return json.dumps(extracted_content)

        @self.client.add_route(route="youtube_playlist")
        def _youtube_playlist(request: Request):
            playlist_id = request.text
            if playlist_id == "":
                raise Exception("No PlaylistID provided")
            playlist = self.youtube.extract_playlist(playlist_id=playlist_id)
            playlist_string = "["
            for n in playlist:
                playlist_string += json.dumps(n)
                playlist_string += ","
            del playlist
            playlist_string = playlist_string.rstrip(",")
            playlist_string += "]"
            return playlist_string

        @self.client.add_route(route="youtube_search")
        def _youtube_search(request: Request):
            search_term = request.text
            if search_term == "":
                raise Exception("No Term provided")
            try:
                url = self.youtube.search(search_term)
                return url
            except (ExtractorError, DownloadError, NotAvailableException):
                raise Exception(Errors.no_results_found)

    def _add_soundcloud_routes(self) -> None:
        """
        Add the routes used for soundcloud.
        :return:
        """

        @self.client.add_route(route="soundcloud_track")
        def _soundcloud_track(request: Request):
            url = request.text
            if url == "":
                raise Exception("No Link provided")
            infos = self.soundcloud.research_track(url)
            if isinstance(infos, dict):
                return json.dumps(infos)
            raise Exception(infos)

        @self.client.add_route(route="soundcloud_playlist")
        def _soundcloud_playlist(request: Request):
            url = request.text
            if url == "":
                raise Exception("No Link provided")
            infos = self.soundcloud.playlist(url=url)
            if isinstance(infos, list):
                return json.dumps(infos)
            raise Exception(infos)

    def _add_discord_routes(self):
        """
        Add routes used for discord.
        :return:
        """

        @self.client.add_route(route="discord_connect")
        async def _discord_connect(request: Request):
            await self.discord.connect(request.text)

        @self.client.add_route(route="discord_disconnect")
        async def _discord_disconnect(request: Request):
            await self.discord.disconnect(request.text)

        @self.client.add_route(route="discord_play")
        async def _discord_play(request: Request):
            await self.discord.play(request.text)

        @self.client.add_route(route="discord_stop")
        async def _discord_stop(request: Request):
            await self.discord.skip(request.text)

        @self.client.add_route(route="discord_volume")
        async def _discord_volume(request: Request):
            await self.discord.volume(request.text)

        @self.client.add_route(route="discord_seek")
        async def _discord_seek(request: Request):
            await self.discord.seek(request.text)

        @self.client.add_route(route="discord_pause")
        async def _discord_pause(request: Request):
            await self.discord.pause(request.text)

        @self.client.add_route(route="discord_resume")
        async def _discord_resume(request: Request):
            await self.discord.resume(request.text)


node = Node()
asyncio.get_event_loop().create_task(node.login())

asyncio.get_event_loop().run_forever()
