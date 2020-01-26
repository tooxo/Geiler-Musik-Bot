import math
import json
import os
import traceback
import re
import socket
import threading
import time
import yaml
from urllib.parse import quote

import bjoern
import requests
from bs4 import BeautifulSoup
from expiringdict import ExpiringDict
from flask import Flask, Response, request
from youtube_dl import YoutubeDL
from youtube_dl.utils import ExtractorError, DownloadError
import youtube_dl


def __real_initialize(self):
    self._CLIENT_ID = "YUKXoArFcqrlQn9tfNHvvyfnDISj04zk"


youtube_dl.extractor.soundcloud.SoundcloudIE._real_initialize = __real_initialize


class Errors:
    no_results_found = "No Results found."
    default = "An Error has occurred."
    info_check = "An Error has occurred while checking Info."
    spotify_pull = (
        "**There was an error pulling the Playlist, 0 Songs were added. "
        "This may be caused by the playlist being private or deleted.**"
    )
    cant_reach_youtube = "Can't reach YouTube. Server Error on their side maybe?"
    youtube_url_invalid = "This YouTube Url is invalid."
    youtube_video_not_available = "The requested YouTube Video is not available."
    error_please_retry = "error_please_retry"
    backend_down = "Our backend seems to be down right now, try again in a few minutes."

    @staticmethod
    def as_list():
        l = []
        for att in Errors.__dict__:
            if isinstance(Errors.__dict__[att], list):
                l.append(Errors.__dict__[att])
        return l


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
                return item["url"], item["acodec"]
        for item in formats:
            # return some audio stream
            if "audio only" in item["format"]:
                return item["url"], item["acodec"]

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
                }
                yt_s, c = self.get_format(info_dict["formats"])
                song["youtube_stream"] = yt_s
                song["codec"] = c

                # preferring format 250: 78k bitrate (discord default = 64, max = 96) + already opus formatted

                if "manifest" in song["youtube_stream"]:
                    song["youtube_stream"] = self.extract_manifest(
                        song["youtube_stream"]
                    )
                song["duration"] = info_dict["duration"]
            for n in info_dict["thumbnails"]:
                song["thumbnail"] = n["url"]
            song["term"] = ""
            song["loadtime"] = int(time.time() - start)
            self.research_cache[song["id"]] = song
            print("Loaded", url, "in", time.time() - start, "secs.")
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

    def search_youtube(self, term):
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
                url, codec, abr = self.decide_on_format(info_dict.get("formats", []))
                stream_dict = {"stream": url, "codec": codec, "abr": abr}
                song = {**song, **stream_dict}
                self.cache[url] = song
                return song
        except (ExtractorError, DownloadError):
            return Errors.default

    @staticmethod
    def playlist(url):
        try:
            youtube_dl_opts = {"extract_flat": True, "logger": YoutubeDLLogger()}
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
        if os.path.exists("./configuration.yaml"):
            filename = "./configuration.yaml"
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
        assert y is not None

        self._host = y.get("parent_host", "")
        self.parent_port = y.get("parent_port", "")
        self.node_id = y.get("node_id", "")
        self.port = y.get("port", y.get("PORT", ""))

        if "custom_port" not in y:
            self.custom_port = y.get("port", y.get("PORT", ""))
        else:
            self.custom_port = y.get("custom_port", "")

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

    @staticmethod
    def youtube_check():
        with requests.get("https://www.youtube.com") as req:
            if req.status_code in (200, 301, 302):
                return True
        return False

    def login(self):
        if self.youtube_check() is True:
            document = {
                "name": self.node_id,
                "ip": self.own_ip,
                "port": self.custom_port,
            }
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self._host, 9988))
                s.sendall(self.api_key.encode())
                if s.recv(1024).decode() != "ACCEPTED":
                    print("API Key is wrong. Check your configuration.")
                    exit(100)
                    return False
                s.sendall(json.dumps(document).encode("UTF-8"))
                while True:
                    try:
                        data = s.recv(1024)
                    except BrokenPipeError:
                        return
                    if data is None:
                        continue
                    s.sendall(data)
                    time.sleep(1)

    @staticmethod
    def get_index(_list, index, default):
        try:
            return _list[index]
        except IndexError:
            return default

    @staticmethod
    def to_hex(x: int):
        if x < 0:
            h = hex(((abs(x) ^ 0xFFFF) + 1) & 0xFFFF)
            first = int("0x" + Node.get_index(h, 2, "0") + Node.get_index(h, 3, "0"), 0)
            second = int(
                "0x" + Node.get_index(h, 4, "0") + Node.get_index(h, 5, "0"), 0
            )
            return [first, second]
        elif x == 0:
            return [0x00, 0x00]
        else:
            h = list(hex(x))
            first = int("0x" + Node.get_index(h, 2, "0") + Node.get_index(h, 3, "0"), 0)
            second = int(
                "0x" + Node.get_index(h, 4, "0") + Node.get_index(h, 5, "0"), 0
            )
            return [first, second]

    def add_routes(self):
        @self.app.route("/research/youtube_video", methods=["POST"])
        def research__youtube_video():
            video_id = request.data.decode()
            if video_id is "":
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
            if playlist_id is "":
                return Response("No PlaylistID provided", 400)
            try:
                playlist = self.youtube.extract_playlist(playlist_id=playlist_id)
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
            volume = request.args.get("volume", "")
            if volume == "":
                volume = 0.5

            volume = float(volume)

            volume = math.log(volume, 10) * 20

            hex_volume = self.to_hex(round(volume))

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

                def generator():
                    try:
                        gen = req.iter_content(chunk_size=1024)
                        header_over = False
                        while True:
                            chunk = b""
                            try:
                                chunk = next(gen)
                            except StopIteration:
                                pass
                            if chunk:
                                if not header_over:
                                    if b"\x4F\x70\x75\x73\x48\x65\x61\x64" in chunk:
                                        # output gain index + 16; index + 17
                                        chunk: bytes
                                        index = chunk.index(
                                            b"\x4F\x70\x75\x73\x48\x65\x61\x64"
                                        )
                                        chunk_list = bytearray(chunk)
                                        chunk_list[index + 16] = hex_volume[0]
                                        chunk_list[index + 17] = hex_volume[1]
                                        chunk = bytes(chunk_list)
                                        header_over = True
                                yield chunk
                            else:
                                break
                    except requests.exceptions.ChunkedEncodingError:
                        print(
                            "ChunkEncodingError with url: {}".format(
                                stream_dict["link"]
                            )
                        )

                return Response(
                    generator(),
                    content_type=req.headers["Content-Type"],
                    headers={"Content-Length": req.headers["Content-Length"]},
                )
            return Response("Error", 400)

    def startup(self):
        self.add_routes()
        print("Startup done.")
        # self.app.run("0.0.0.0", int(self.port))
        bjoern.run(self.app, "0.0.0.0", int(self.port), True)


def login_loop(n: Node):
    while True:
        n.login()
        time.sleep(30)


if __name__ == "__main__":
    print("Beginning to start up.")
    node = Node()
    threading.Thread(target=login_loop, args=(node,)).start()
    node.startup()
