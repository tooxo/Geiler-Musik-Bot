import asyncio
import functools
import json
import logging
import os
import random
import re
import string
import time
import traceback
from urllib.parse import quote

import aiohttp
import requests
import yaml
from bs4 import BeautifulSoup
from expiringdict import ExpiringDict
from flask import Flask, Response, request
from youtube_dl import YoutubeDL
from youtube_dl.utils import DownloadError, ExtractorError

from discord_handler import DiscordHandler

logging.getLogger("discord").setLevel(logging.INFO)


class Errors:
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
    @staticmethod
    def debug(msg):
        if "youtube:search" in msg and "query" in msg:
            print(
                "[YouTube Search] Searched Term: '"
                + msg.split('"')[1].split('"')[-1]
                + "'"
            )

    @staticmethod
    def warning(msg):
        print("warn", msg)

    @staticmethod
    def error(msg):
        if "This video is no longer available" in msg:
            raise NotAvailableException("notavailable")
        raise ExtractorError("Video Downloading failed.")


class NotAvailableException(Exception):
    pass


class YouTube:
    def __init__(self):
        self.research_cache = ExpiringDict(1000, 10000)
        self.search_cache = dict()
        self.music_search_cache = dict()
        self.cipher = self.create_cipher()

    @staticmethod
    def create_cipher():
        st = ""
        for x in range(16):
            st += random.choice(string.ascii_lowercase)
        return st

    @staticmethod
    def extract_manifest(manifest_url):
        manifest_pattern = re.compile(
            r"<Representation id=\"\d+\" codecs=\"\S+\" audioSamplingRate=\"(\d+)\" startWithSAP=\"\d\" "
            r"bandwidth=\"\d+\">(<AudioChannelConfiguration[^/]+/>)?<BaseURL>(\S+)</BaseURL>"
        )
        with requests.get(manifest_url) as res:
            text = res.text
            it = re.finditer(manifest_pattern, text)
            return_stream_url = ""
            return_sample_rate = 0
            for match in it:
                if int(match.group(1)) >= return_sample_rate:
                    return_stream_url = match.group(3)
                    return_sample_rate = int(match.group(1))
            return return_stream_url

    @staticmethod
    def get_format(formats: list):
        for item in formats:
            if item["format_id"] == "250":
                return item["url"], item["acodec"], item["abr"]
        for item in formats:
            # return some audio stream
            if "audio only" in item["format"]:
                return item["url"], item["acodec"], item["abr"]

    def youtube_extraction(self, video_id, url, own_ip, custom_port):
        try:
            start = time.time()
            if self.research_cache.get(video_id, None) is not None:
                return self.research_cache.get(video_id)
            with YoutubeDL({"logger": YoutubeDLLogger()}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                song = {
                    "link": url,
                    "id": info_dict["id"],
                    "title": info_dict["title"],
                    "stream": (
                        "http://"
                        + own_ip
                        + ":"
                        + custom_port
                        + "/stream/youtube_video?id="
                        + video_id
                    ),
                    "cipher": self.cipher,
                }
                yt_s, c, abr = self.get_format(info_dict["formats"])
                song["youtube_stream"] = yt_s
                song["codec"] = c
                song["abr"] = abr
                # preferring format 250: 78k bitrate (discord default = 64, max = 96) + already opus formatted

                if "manifest" in song["youtube_stream"]:
                    # youtube-dl doesn't handle manifest extraction, so I need to do it.
                    song["youtube_stream"] = self.extract_manifest(
                        song["youtube_stream"]
                    )
                song["duration"] = info_dict["duration"]
            for n in info_dict["thumbnails"]:
                song["thumbnail"] = n["url"]
            song["term"] = ""
            song["loadtime"] = int(time.time() - start)
            self.research_cache[song["id"]] = song
            return song
        except NotAvailableException:
            return Errors.youtube_video_not_available
        except (DownloadError, ExtractorError) as e:
            traceback.print_exc()
            return Errors.default
        except Exception as ex:
            print(ex)
            return Errors.error_please_retry

    @staticmethod
    def extract_playlist(playlist_id):

        url = "https://youtube.com/playlist?list=" + playlist_id
        youtube_dl_opts = {
            "extract_flat": True,
            "ignore_errors": True,
            "logger": YoutubeDLLogger(),
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
        return output

    def search_youtube_basic(self, term):
        if term in self.search_cache:
            return self.search_cache[term]
        query = quote(term)
        url = (
            "https://www.youtube.com/results?search_query="
            + query
            + "&sp=EgIQAQ%253D%253D"
        )  # SP = Video only
        for x in range(0, 2, 1):
            url_list = []
            with requests.get(url) as res:
                if res.status_code != 200:
                    continue
                text = res.text
                soup = BeautifulSoup(text, "html.parser")
                for vid in soup.findAll(attrs={"class": "yt-uix-tile-link"}):
                    url_list.append(vid["href"])
            for url in url_list:
                if url.startswith("/watch"):
                    self.search_cache[term] = "https://www.youtube.com" + url
                    return "https://www.youtube.com" + url
        raise NotAvailableException("no videos found")

    @staticmethod
    def _create_music_payload(query: str):
        payload: dict = json.loads(
            '{"context":{"client":{"clientName":"WEB_REMIX","clientVersion":"0.1","hl":"de","gl":"DE",'
            '"experimentIds":[],"experimentsToken":"","utcOffsetMinutes":60,'
            '"locationInfo":{"locationPermissionAuthorizationStatus":'
            '"LOCATION_PERMISSION_AUTHORIZATION_STATUS_UNSUPPORTED"},'
            '"musicAppInfo":{"musicActivityMasterSwitch":"MUSIC_ACTIVITY_MASTER_SWITCH_INDETERMINATE",'
            '"musicLocationMasterSwitch":"MUSIC_LOCATION_MASTER_SWITCH_INDETERMINATE",'
            '"pwaInstallabilityStatus":"PWA_INSTALLABILITY_STATUS_UNKNOWN"}},"capabilities":{},'
            '"request":{"internalExperimentFlags":[{"key":"force_music_enable_outertube_search_suggestions",'
            '"value":"true"},{"key":"force_music_enable_outertube_playlist_detail_browse","value":"true"},'
            '{"key":"force_music_enable_outertube_tastebuilder_browse","value":"true"}],"sessionIndex":{}},'
            '"clickTracking":{"clickTrackingParams":"IhMIk5OBqvnT5wIVgfFVCh2s8AzdMghleHRlcm5hbA=="},'
            '"activePlayers":{},"user":{"enableSafetyMode":false}},"query":""}'
        )
        payload["query"] = query
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

    def search_youtube_music(self, term):
        if term in self.music_search_cache:
            return self.music_search_cache[term]
        url = "https://music.youtube.com/youtubei/v1/search?alt=json&key=AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30"
        for x in range(1, 2, 1):
            with requests.post(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/80.0.3987.87 Safari/537.36",
                    "Referer": f"https://music.youtube.com/search?q={quote(term)}",
                    "Content-Type": "application/json",
                },
                data=self._create_music_payload(query=term),
            ) as res:
                if res.status_code != 200:
                    continue
                response: dict = res.json()
                video_id = self._get_stream_from_youtube_music_response(
                    response
                )
                self.search_cache[term] = (
                    "https://www.youtube.com"
                    + f"https://youtube.com/watch?v={video_id}"
                )
                return f"https://youtube.com/watch?v={video_id}"

    def search_youtube(self, input_json):
        input_json = json.loads(input_json)
        if input_json.get("service", "basic") == "music":
            return self.search_youtube_music(input_json["term"])
        return self.search_youtube_basic(input_json["term"])


class SoundCloud:
    def __init__(self):
        self.cache = ExpiringDict(1000, 10000)

    @staticmethod
    def decide_on_format(formats: list):
        for f in formats:
            f: dict
            if "opus" in f.get("ext"):
                return f.get("url", ""), f.get("ext", "opus"), f.get("abr", 0)
        return (
            formats[0].get("url", ""),
            formats[0].get("ext", "mp3"),
            formats[0].get("abr", 0),
        )

    def research_track(self, url: str):
        if url in self.cache:
            return self.cache.get(url, {})
        try:
            _time = time.time()
            youtube_dl_opts = {"logger": YoutubeDLLogger()}
            with YoutubeDL(youtube_dl_opts) as ydl:
                info_dict: dict = ydl.extract_info(url=url, download=False)
                song = {
                    "title": info_dict.get("uploader", "")
                    + " - "
                    + info_dict.get("title", ""),
                    "link": info_dict.get("webpage_url", ""),
                    "duration": info_dict.get("duration", 0),
                    "thumbnail": info_dict.get("thumbnails")[-1].get("url", ""),
                    "loadtime": time.time() - _time,
                    "term": info_dict.get("uploader", "")
                    + " - "
                    + info_dict.get("title", ""),
                }
                url, codec, abr = self.decide_on_format(
                    info_dict.get("formats", [])
                )
                stream_dict = {"stream": url, "codec": codec, "abr": abr}
                song = {**song, **stream_dict}
                self.cache[url] = song
                return song
        except (ExtractorError, DownloadError):
            return Errors.default

    @staticmethod
    def playlist(url):
        try:
            youtube_dl_opts = {
                "extract_flat": True,
                "logger": YoutubeDLLogger(),
            }
            with YoutubeDL(youtube_dl_opts) as ydl:
                info_dict: dict = ydl.extract_info(url=url, download=False)
                songs = []
                for song in info_dict.get("entries", []):
                    songs.append({"link": song.get("url", "")})
                return songs
        except (ExtractorError, DownloadError):
            return Errors.default


class Node:
    def __init__(self):
        # loading config
        filename = ""
        if os.path.exists("configuration.yaml"):
            filename = "configuration.yaml"
        elif os.path.exists("./configuration.yml"):
            filename = "./configuration.yml"
        else:
            print("Configuration File Missing.")
            exit(1)
        f = open(filename, "r")
        y = None
        try:
            y = yaml.safe_load(f)
        except yaml.YAMLError as ex:
            print(ex)
            exit(1)

        self._host = y.get("parent_host", "")
        self.parent_port = y.get("parent_port", "")
        self.node_id = y.get("node_id", "")

        if "custom_port" not in y:
            self.custom_port = y.get("port", y.get("PORT", ""))
        else:
            self.custom_port = y.get("custom_port", "")

        if self.custom_port == "":
            self.custom_port = os.environ.get("PORT", 0)

        self.host = "http://" + self._host

        if "own_ip" not in y:
            r = requests.get("https://api.ipify.org?format=json")
            self.own_ip = r.json()["ip"]
        else:
            self.own_ip = y.get("own_ip", "")
        self.api_key = y.get("API_KEY", "API_KEY")

        self.app = Flask(__name__)
        self.youtube = YouTube()
        self.soundcloud = SoundCloud()
        self.discord = None

    @staticmethod
    async def youtube_check() -> bool:
        async with aiohttp.request("GET", "https://www.youtube.com") as req:
            await req.text()
            if req.status in (200, 301, 302):
                return True
            req.close()
        return False

    async def login(self):
        if await self.youtube_check() is True:
            document = {
                "name": self.node_id,
                "ip": self.own_ip,
                "port": self.custom_port,
            }

            reader, writer = await asyncio.open_connection(
                self._host, self.parent_port, loop=asyncio.get_event_loop()
            )
            reader: asyncio.StreamReader
            writer: asyncio.StreamWriter

            writer.write(f"A_{self.api_key}".encode())
            await writer.drain()
            if (await reader.read(1024)).decode() != "A_ACCEPT":
                print("API Key is wrong. Check your configuration.")
                exit(100)
                return False
            writer.write(json.dumps(document).encode("UTF-8"))
            await writer.drain()

            discord_api_key = ""
            while not DiscordHandler.validate_token(discord_api_key):
                discord_api_key = (await reader.read(1024)).decode()[3:]

            writer.write(b"BT_ACCEPT")
            await writer.drain()

            self.discord = DiscordHandler(discord_api_key, writer, reader, self)

            async def socket_thread(discord: DiscordHandler):
                while True:
                    await asyncio.sleep(0.1)
                    try:
                        data = await reader.read(4096)
                    except BrokenPipeError:
                        break
                    if not data:
                        continue
                    d = data.decode()
                    if d.startswith("C"):
                        try:
                            await discord.handle_command(d)
                        except Exception as e:
                            traceback.print_exc()

            asyncio.ensure_future(
                socket_thread(self.discord)
            ).add_done_callback(lambda _: exit(1))

            await self.discord.start()

    def add_routes(self):
        @self.app.route("/research/youtube_video", methods=["POST"])
        def research__youtube_video():
            video_id = request.data.decode()
            if video_id == "":
                return Response("No VideoID provided", 400)
            extracted_content: dict = self.youtube.youtube_extraction(
                video_id=video_id,
                url="https://www.youtube.com/watch?v=" + video_id,
                own_ip=self.own_ip,
                custom_port=self.custom_port,
            )
            if isinstance(extracted_content, str):
                return Response(extracted_content, 400)
            return Response(json.dumps(extracted_content), 200)

        @self.app.route("/research/youtube_playlist", methods=["POST"])
        def research__youtube_playlist():
            playlist_id = request.data.decode()
            if playlist_id == "":
                return Response("No PlaylistID provided", 400)
            try:
                playlist = self.youtube.extract_playlist(
                    playlist_id=playlist_id
                )
                playlist_string = "["
                for n in playlist:
                    playlist_string += json.dumps(n)
                    playlist_string += ","
                playlist_string = playlist_string.rstrip(",")
                playlist_string += "]"
                return Response(playlist_string, 200)
            except (ExtractorError, DownloadError):
                return Response("[]", 400)

        @self.app.route("/research/youtube_search", methods=["POST"])
        def research__youtube_search():
            search_term = request.data.decode()
            if search_term == "":
                return Response("No Term provided", 400)
            try:
                url = self.youtube.search_youtube(search_term)
                return Response(url, 200)
            except (ExtractorError, DownloadError, NotAvailableException):
                return Response(Errors.no_results_found, 400)

        @self.app.route("/research/soundcloud_track", methods=["POST"])
        def research__soundcloud_track():
            url = request.data.decode()
            if url == "":
                return Response("No Link provided", 400)
            infos = self.soundcloud.research_track(url)
            if isinstance(infos, dict):
                return Response(json.dumps(infos), 200)
            return Response(infos, 400)

        @self.app.route("/research/soundcloud_playlist", methods=["POST"])
        def research__soundcloud_playlist():
            url = request.data.decode()
            if url == "":
                return Response("No Link provided", 400)
            infos = self.soundcloud.playlist(url=url)
            if isinstance(infos, list):
                return Response(json.dumps(infos), 200)
            return Response(infos, 400)

        @self.app.route("/stream")
        @self.app.route("/stream/youtube_video")
        def stream():
            url = request.args.get("id", "")
            if url == "":
                return Response("No URL provided", 400)
            stream_dict = self.youtube.youtube_extraction(
                video_id=url,
                url="https://www.youtube.com/watch?v=" + url,
                own_ip=self.own_ip,
                custom_port=self.custom_port,
            )

            if not isinstance(stream_dict, str):
                req = requests.get(stream_dict["youtube_stream"], stream=True)
                return Response(
                    req.iter_content(chunk_size=1024),
                    content_type=req.headers["Content-Type"],
                    headers={"Content-Length": req.headers["Content-Length"]},
                )
            return Response("Error", 400)

    async def startup(self):
        self.add_routes()
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        asyncio.get_event_loop().run_in_executor(
            None,
            functools.partial(
                self.app.run,
                host="0.0.0.0",  # nosec
                port=int(self.custom_port),
                threaded=True,
            ),
        )


async def login_loop(n: Node):
    while True:
        await n.login()
        await asyncio.sleep(30)


node = Node()

asyncio.get_event_loop().create_task(node.startup())
asyncio.get_event_loop().create_task(login_loop(node))

try:
    asyncio.get_event_loop().run_forever()
except (KeyboardInterrupt, SystemExit):
    asyncio.get_event_loop().close()
    print("Goodbye!")
