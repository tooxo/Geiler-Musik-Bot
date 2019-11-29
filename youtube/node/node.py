from flask import Flask, request, Response
import requests
import json
import re
import time
import multiprocessing
from expiringdict import ExpiringDict
from youtube_dl import YoutubeDL, DownloadError
from youtube_dl.utils import ExtractorError
from errors import Errors
from bs4 import BeautifulSoup
from urllib.parse import quote
import os
import bjoern

node = None


class YoutubeDLLogger(object):
    def debug(self, msg):
        if "youtube:search" in msg and "query" in msg:
            print(
                "[YouTube Search] Searched Term: '"
                + msg.split('"')[1].split('"')[-1]
                + "'"
            )

    def warning(self, msg):
        print("warn", msg)

    def error(self, msg):
        if "This video is no longer available" in msg:
            raise NotAvailableException("notavailable")
        raise ExtractorError("Video Downloading failed.")


class NotAvailableException(Exception):
    def __init__(self, message):
        super.__init__(message)


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

    def youtube_extraction(self, video_id, url, own_ip, custom_port):
        try:
            start = time.time()
            if self.research_cache.get(video_id, None) is not None:
                return self.research_cache.get(video_id)
            with YoutubeDL({"logger": YoutubeDLLogger()}) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                song = {"link": url, "id": info_dict["id"], "title": info_dict["title"]}
                for item in info_dict["formats"]:
                    if "audio only" in item["format"]:
                        song["stream"] = (
                            "http://"
                            + own_ip
                            + ":"
                            + custom_port
                            + "/stream/youtube_video?id="
                            + video_id
                        )
                        song["youtube_stream"] = item["url"]
                if "manifest" in song["stream"]:
                    song["stream"] = self.extract_manifest(song["stream"])
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
        except (DownloadError, ExtractorError) as de:
            node.logout()
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
        url_list = []
        with requests.get(url) as res:
            text = res.text
            soup = BeautifulSoup(text, "html.parser")
            for vid in soup.findAll(attrs={"class": "yt-uix-tile-link"}):
                url_list.append(vid["href"])
        for url in url_list:
            if url.startswith("/watch"):
                self.search_cache[term] = "https://www.youtube.com" + url
                return "https://www.youtube.com" + url


class Node:
    def __init__(self):
        self.host = os.environ.get("parent_host", "")
        self.parent_port = os.environ.get("parent_port", "")
        self.node_id = os.environ.get("node_id", "")
        self.port = os.environ.get("port", os.environ.get("PORT", ""))

        if "custom_port" not in os.environ:
            self.custom_port = os.environ.get("port", os.environ.get("PORT", ""))
        else:
            self.custom_port = os.environ["custom_port"]
        if "http" not in self.host:
            self.host = "http://" + self.host

        if "own_ip" not in os.environ:
            r = requests.get("https://api.ipify.org?format=json")
            self.own_ip = r.json()["ip"]
        else:
            self.own_ip = os.environ["own_ip"]

        self.app = Flask(__name__)
        self.youtube = YouTube()

        self.process = None
        self.should_be_connected = False

    @staticmethod
    def youtube_check():
        with requests.get("https://www.youtube.com") as req:
            if (
                req.status_code is 200
                or req.status_code is 301
                or req.status_code is 302
            ):
                return True
        return False

    def login(self):
        if self.youtube_check() is True:
            document = {
                "node_id": self.node_id,
                "ip": self.own_ip,
                "port": self.custom_port,
            }
            with requests.post(
                url=self.host + ":" + str(self.parent_port) + "/register_node",
                data=json.dumps(document),
            ) as pos:
                if pos.status_code is 200:
                    print("[-] - Login Successful - [-]")
                    self.should_be_connected = True
                    self.enable_alive()
                    return True
            return False

    def logout(self):
        with requests.post(
            url=self.host + ":" + str(self.parent_port) + "/logout"
        ) as post:
            if post.status_code == 200:
                if post.text == "True":
                    self.should_be_connected = False

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
            if type(extracted_content) == str:
                return Response(extracted_content, 400)
            return Response(json.dumps(extracted_content), 200)

        @self.app.route("/research/youtube_playlist", methods=["POST"])
        def research__youtube_playlist():
            playlist_id = request.data.decode()
            if playlist_id is "":
                return Response("No PlaylistID provided", 400)
            playlist = self.youtube.extract_playlist(playlist_id=playlist_id)
            playlist_string = "["
            for n in playlist:
                playlist_string += json.dumps(n)
                playlist_string += ","
            playlist_string = playlist_string.rstrip(",")
            playlist_string += "]"
            return Response(playlist_string, 200)

        @self.app.route("/research/youtube_search", methods=["POST"])
        def research__youtube_search():
            search_term = request.data.decode()
            if search_term == "":
                return Response("No Term provided", 400)
            url = self.youtube.search_youtube(search_term)
            return Response(url, 200)

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

            if type(stream_dict) is not str:
                req = requests.get(stream_dict["youtube_stream"], stream=True)
                return Response(
                    req.iter_content(chunk_size=512),
                    content_type=req.headers["Content-Type"],
                    headers={"Content-Length": req.headers["Content-Length"]},
                )
            else:
                return Response("Error", 400)

        @self.app.route("/health_check")
        def health_check():
            return str(int(time.time()))

    def _alive_check(self):
        while True:
            time.sleep(25)
            try:
                if self.should_be_connected is True:
                    ro = requests.get(
                        self.host
                        + ":"
                        + self.parent_port
                        + "/am_i_still_here?id="
                        + self.node_id
                    )
                    if ro.text != "YES":
                        if self.youtube_check():
                            self.login()
                else:
                    self.login()
            except:
                pass

    def startup(self):
        self.add_routes()
        print("[[ Im Ready! ]]")
        # self.app.run("0.0.0.0", int(self.port))
        bjoern.run(self.app, "0.0.0.0", int(self.port), True)

    def enable_alive(self):
        self.process = multiprocessing.Process(target=self._alive_check)
        self.process.start()


if __name__ == "__main__":
    print("Beginning to start up.")
    node = Node()
    while 1 == 1:
        if node.login() is True:
            print("[[ Starting up ]]")
            node.startup()
        time.sleep(30)
