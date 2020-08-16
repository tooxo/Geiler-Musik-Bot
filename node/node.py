"""
Node
"""
import asyncio
import json
import os
import re
import sys
import time
import traceback
from typing import List, Tuple, Union
from urllib.parse import quote
from yaml import YAMLError, safe_load

import aiohttp
import pytube
from expiringdict import ExpiringDict
from karp.client import KARPClient
from karp.request import Request
from pytube.exceptions import RegexMatchError

from discord_handler import DiscordHandler


class Errors:
    """
    All Errors
    """

    no_results_found = "No Results found."
    default = "An Error has occurred."
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


class NotAvailableException(Exception):
    """
    Exception raised if a video is unavailable
    """


class YouTube:
    """
    Class to interact with YouTube
    """

    def __init__(self) -> None:
        self.research_cache: ExpiringDict = ExpiringDict(1000, 10000)
        self.search_cache: dict = {}
        self.music_search_cache: dict = {}

    @staticmethod
    async def extract_manifest(manifest_url: str) -> str:
        """
        Extract a stream url from a manifest url
        :param manifest_url:
        :return:
        """
        manifest_pattern = re.compile(
            r"<Representation id=\"\d+\" codecs=\"\S+\" "
            r"audioSamplingRate=\"(\d+)\" startWithSAP=\"\d\" "
            r"bandwidth=\"\d+\">(<AudioChannelConfiguration"
            r"[^/]+/>)?<BaseURL>(\S+)</BaseURL>"
        )
        print("extracting from manifest:", manifest_url)
        async with aiohttp.request("GET", manifest_url) as res:
            text = (await res.read()).decode()
            iterator = re.finditer(manifest_pattern, text)
            return_stream_url = ""
            return_sample_rate = 0
            for match in iterator:
                if int(match.group(1)) >= return_sample_rate:
                    return_stream_url = match.group(3)
                    return_sample_rate = int(match.group(1))
            return return_stream_url

    @staticmethod
    def get_format(formats: pytube.StreamQuery) -> Tuple[str, str, int]:
        """
        Decide on a format from all formats
        :param formats: formats
        :return:
        """
        if formats.get_by_itag(250):
            extracted_format = formats.get_by_itag(250)
            return (
                extracted_format.url,
                extracted_format.audio_codec,
                extracted_format.abr[:-4],
            )
        if formats.get_by_itag(251):
            extracted_format = formats.get_by_itag(251)
            return (
                extracted_format.url,
                extracted_format.audio_codec,
                extracted_format.abr[:-4],
            )
        if formats.get_by_itag(249):
            extracted_format = formats.get_by_itag(249)
            return (
                extracted_format.url,
                extracted_format.audio_codec,
                extracted_format.abr[:-4],
            )
        return (
            formats.filter(only_audio=True).first().url,
            formats.filter(only_audio=True).first().audio_codec,
            formats.filter(only_audio=True).first().abr[:-4],
        )

    async def youtube_extraction(self, video_id: str, url: str) -> dict:
        """
        Extract data from YouTube
        :param video_id:
        :param url:
        :return:
        """
        # noinspection PyBroadException
        try:
            start = time.time()
            if self.research_cache.get(video_id, None) is not None:
                return self.research_cache.get(video_id)
            ydl = await pytube.YouTube.create(url)
            yt_s, codec_name, abr = self.get_format(ydl.streams)
            # preferring format 250: 78k bitrate
            # (discord default = 64, max = 96) + already opus formatted
            song = {
                "link": url,
                "id": ydl.video_id,
                "title": ydl.title,
                "stream": yt_s,
                "codec": codec_name,
                "abr": abr,
                "duration": ydl.length,
                "thumbnail": ydl.thumbnail_url,
                "term": "",
            }

            if "manifest" in song["stream"]:
                # pytube doesn't handle manifest extraction, so I need to do it.
                song["stream"] = self.extract_manifest(song["stream"])
            async with aiohttp.request(
                "HEAD", song["stream"], allow_redirects=False
            ) as async_request:
                song["stream"] = async_request.headers.get(
                    "Location", song["stream"]
                )
            song["loadtime"] = int(time.time() - start)
            self.research_cache[song["id"]] = song
            del ydl
            return song
        except (NotAvailableException, RegexMatchError):
            pass
        except Exception:
            traceback.print_exc()
        raise NotAvailableException(Errors.no_results_found)

    @staticmethod
    async def extract_playlist(playlist_id: str) -> List[dict]:
        """
        Extract tracks from playlist url
        :param playlist_id: playlist id
        :return:
        """
        url = "https://youtube.com/playlist?list=" + playlist_id
        output = []
        ydl = await pytube.Playlist.create(url)
        for url, title in ydl:
            if not url or not title:
                continue
            output.append({"title": title, "link": url})
        del ydl
        return output

    async def search_youtube_basic(self, term: str) -> str:
        """
        Search YouTube
        :param term:
        :return:
        """
        if term in self.search_cache:
            return self.search_cache[term]
        query = quote(term)
        url = (
            f"https://www.youtube.com/results?search_query="
            f"{query}%2C+video&pbj=1"
        )
        for _ in range(0, 2, 1):
            url_list = []
            async with aiohttp.request(
                "GET",
                url,
                headers={
                    "x-youtube-client-name": "1",
                    "x-youtube-client-version": "2.20200312.05.00",
                },
            ) as res:
                if res.status != 200:
                    continue
                text = await res.read()
                data = json.loads(text)

                data = data[1]["response"]["contents"][
                    "twoColumnSearchResultsRenderer"
                ]["primaryContents"]["sectionListRenderer"]["contents"]

                for item in data:
                    if "itemSectionRenderer" not in item:
                        continue  # its not a search result
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

    async def search_youtube_music(self, term: str) -> str:
        """
        Search YouTube Music
        :param term: Search Term
        :return: YouTube url
        """
        if term in self.music_search_cache:
            return self.music_search_cache[term]
        url = (
            "https://music.youtube.com/youtubei/v1/search"
            "?alt=json&key=AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30"
        )
        for _ in range(1, 2, 1):
            async with aiohttp.request(
                "POST",
                url=url,
                headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/80.0.3987.87 Safari/537.36",
                    "Referer": f"https://music.youtube.com/search"
                    f"?q={quote(term)}",
                    "Content-Type": "application/json",
                },
                data=self._create_music_payload(query=term).encode(),
            ) as res:
                if res.status != 200:
                    continue
                response: dict = json.loads(await res.read())
                video_id = self._get_stream_from_youtube_music_response(
                    response
                )
                self.search_cache[term] = (
                    "https://www.youtube.com"
                    + f"https://youtube.com/watch?v={video_id}"
                )
                return f"https://youtube.com/watch?v={video_id}"
        raise NotAvailableException("no videos found")

    async def search(self, input_json: str) -> str:
        """
        Search
        :param input_json: data
        :return: Search result url
        """
        input_json: dict = json.loads(input_json)
        if input_json.get("service", "basic") == "music":
            return await self.search_youtube_music(input_json["term"])
        return await self.search_youtube_basic(input_json["term"])


class SoundCloud:
    """
    Class to interact with SoundCloud
    """

    def __init__(self) -> None:
        self.cache: ExpiringDict = ExpiringDict(1000, 10000)
        self.api_key = ""

    URL_RESOLVE = "https://api.soundcloud.com/resolve?url={}&client_id={}"
    URL_MISSING = "https://api-v2.soundcloud.com/tracks?ids={}&client_id={}"

    SCRIPT_REGEX = re.compile(
        r"(https://a-v2\.sndcdn\.com/assets/\d\d?-[\da-z]{8}-[\da-z].js)"
    )

    ID_REGEX = re.compile(r'client_id:"([a-zA-Z0-9]+)"')

    COMMON_HEADERS = {
        "Host": "api-v2.soundcloud.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/70.0.3538.27 Safari/537.36",
        "Accept-Charset": "utf-8",
        "Accept": "text/html,application/xhtml+xml,application/"
        "xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-us,en;q=0.5",
        "Connection": "close",
    }

    PLAYLIST_PATTERN = re.compile(
        r"https://[a-z-\\]+\.sndcdn.com/media/[\d]+/[\d]+[\S]+"
    )

    async def _get_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        async with aiohttp.request("GET", "https://soundcloud.com") as res:
            response = (await res.read()).decode()

        scripts = re.findall(self.SCRIPT_REGEX, response)
        for script in scripts:
            async with aiohttp.request("GET", script) as res:
                script_src = (await res.read()).decode()
                client_id = re.findall(self.ID_REGEX, script_src)
                if not client_id:
                    continue
                self.api_key = client_id[0]
                return self.api_key

    @staticmethod
    def _decide_on_format(formats: dict):
        for format_name in formats.keys():
            if "opus" in format_name:
                return (
                    formats[format_name],
                    format_name.split("_")[1],
                    format_name.split("_")[2],
                )
        return (
            formats[0],
            list(formats.keys())[0].split("_")[1],
            list(formats.keys())[0].split("_")[2],
        )

    async def research_track(self, url: str) -> Union[dict, str]:
        """
        Extract information from an SoundCloud Track
        :param url: soundcloud url
        :return: search result
        """
        if url in self.cache:
            return self.cache.get(url, {})
        # noinspection PyBroadException
        try:
            _time = time.time()
            async with aiohttp.request(
                "GET",
                self.URL_RESOLVE.format(url, await self._get_api_key()),
                headers=self.COMMON_HEADERS,
            ) as res:
                data = json.loads((await res.read()).decode())

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

            async with aiohttp.request(
                "GET",
                f"{codec_url}?client_id={await self._get_api_key()}",
                headers=self.COMMON_HEADERS,
            ) as res:
                url = json.loads(await res.read())["url"]

            if "playlist.m3u8" in url:
                async with aiohttp.request("GET", url) as res:
                    last_entry = re.findall(
                        self.PLAYLIST_PATTERN, (await res.read()).decode()
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
            pass
        except Exception:
            traceback.print_exc()
        raise NotAvailableException(Errors.default)

    async def playlist(self, url: str) -> Union[List[dict], str]:
        """
        Extract songs from SoundCloud playlist
        :param url: playlist url
        :return: songs
        """
        try:
            async with aiohttp.request(
                "GET",
                url=self.URL_RESOLVE.format(url, await self._get_api_key()),
                headers=self.COMMON_HEADERS,
            ) as res:
                data = json.loads(await res.read())

            tracks = []
            missing = []
            for track in data["tracks"]:
                try:
                    tracks.append(
                        {
                            "title": track["title"],
                            "link": track["permalink_url"],
                        }
                    )
                except KeyError:
                    missing.append(str(track["id"]))

            missing_requests = []
            while missing:
                missing_requests.append(quote(",").join(missing[:50]))
                missing = missing[50:]

            for missing_request in missing_requests:
                async with aiohttp.request(
                    "GET",
                    url=self.URL_MISSING.format(
                        missing_request, await self._get_api_key()
                    ),
                    headers=self.COMMON_HEADERS,
                ) as _res:
                    _text_response = await _res.read()
                    _data = json.loads(_text_response)
                    for _track in _data:
                        tracks.append(
                            {
                                "title": _track["title"],
                                "link": _track["permalink_url"],
                            }
                        )

            return tracks
        except (KeyError, AttributeError, TimeoutError, UnicodeDecodeError):
            traceback.print_exc()
            return Errors.default

    async def search(self, search_term: str) -> dict:
        """
        Search SoundCloud
        :return:
        """

        _time = time.time()

        search_url = (
            f"https://api-v2.soundcloud.com/search?q={quote(search_term)}"
            f"&client_id={await self._get_api_key()}"
        )
        # noinspection PyBroadException
        try:
            async with aiohttp.request("GET", search_url) as req:
                response: dict = json.loads(await req.read())
                result = response["collection"][0]

            codec_url = ""
            codec = ""
            abr = 70

            for transcoding in result["media"]["transcodings"]:
                if "opus" in transcoding["preset"]:
                    codec_url = transcoding["url"]
                    codec = "opus"

            if not codec_url:
                codec_url = result["media"]["transcodings"][0]["url"]
                codec = "mp3"

            async with aiohttp.request(
                "GET",
                f"{codec_url}?client_id={await self._get_api_key()}",
                headers=self.COMMON_HEADERS,
            ) as res:
                url = json.loads(await res.read())["url"]

            if "playlist.m3u8" in url:
                async with aiohttp.request("GET", url) as res:
                    last_entry = re.findall(
                        self.PLAYLIST_PATTERN, (await res.read()).decode()
                    )[-1]
                    url = re.sub(r"/[\d]+/", "/0/", last_entry)

            song = {
                "title": result.get("title", "_"),
                "link": result.get("permalink_url", ""),
                "duration": round(result.get("duration", 0) / 1000),
                "thumbnail": result.get("artwork_url", ""),
                "loadtime": time.time() - _time,
                "term": result.get("title", "_"),
                "stream": url,
                "codec": codec,
                "abr": abr,
            }

            return song
        except IndexError:
            pass
        except Exception:
            traceback.print_exc()
        raise NotAvailableException("no results found")


class Node:
    """
    Node
    """

    def __init__(self) -> None:
        # loading config
        if os.path.exists("configuration.yaml"):
            filename = "configuration.yaml"
        elif os.path.exists("./configuration.yml"):
            filename = "./configuration.yml"
        else:
            print("Configuration File Missing.")
            sys.exit(1)
        file = open(filename, "r")
        try:
            loaded_yaml = safe_load(file)
        except YAMLError:
            traceback.print_exc()
            sys.exit(1)

        self.parent_host = loaded_yaml.get("parent_host", "")
        self.parent_port = loaded_yaml.get("parent_port", "")

        self.api_key = loaded_yaml.get("API_KEY", "API_KEY")

        self.youtube = YouTube()
        self.soundcloud = SoundCloud()
        self.discord = None

        self.client = KARPClient(self.parent_host, self.parent_port)
        self.client.on_disconnect = self._on_disconnect

    @staticmethod
    def _on_disconnect() -> None:
        sys.exit(0)

    async def login(self) -> None:
        """
        Login to the NodeController
        :return:
        """
        self._add_authentication_routes()
        future = await self.client.open()

        # add empty function to prevent the traceback from showing on exit
        future.add_done_callback(print)

    def _add_authentication_routes(self) -> None:
        """
        Add the routes used for authentication.
        :return:
        """

        # noinspection PyUnusedLocal
        @self.client.add_route(route="identify")
        def _identify(request: Request):  # pylint: disable=unused-argument
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
        async def _youtube_video(request: Request):
            video_id = request.text
            if video_id == "":
                raise Exception("No VideoID provided")
            extracted_content: dict = await self.youtube.youtube_extraction(
                video_id=video_id,
                url="https://www.youtube.com/watch?v=" + video_id,
            )
            return json.dumps(extracted_content)

        @self.client.add_route(route="youtube_playlist")
        async def _youtube_playlist(request: Request):
            playlist_id = request.text
            if playlist_id == "":
                raise Exception("No PlaylistID provided")
            playlist = await self.youtube.extract_playlist(
                playlist_id=playlist_id
            )
            return json.dumps(playlist)

        @self.client.add_route(route="youtube_search")
        async def _youtube_search(request: Request):
            search_term = request.text
            if search_term == "":
                raise Exception("No Term provided")
            url = await self.youtube.search(search_term)
            return url

    def _add_soundcloud_routes(self) -> None:
        """
        Add the routes used for soundcloud.
        :return:
        """

        @self.client.add_route(route="soundcloud_track")
        async def _soundcloud_track(request: Request):
            url = request.text
            if url == "":
                raise Exception("No Link provided")
            infos = await self.soundcloud.research_track(url)
            return json.dumps(infos)

        @self.client.add_route(route="soundcloud_playlist")
        async def _soundcloud_playlist(request: Request):
            url = request.text
            if url == "":
                raise Exception("No Link provided")
            infos = await self.soundcloud.playlist(url=url)
            if isinstance(infos, list):
                return json.dumps(infos)
            raise Exception(infos)

        @self.client.add_route(route="soundcloud_search")
        async def _soundcloud_search(request: Request):
            term = request.text
            infos = await self.soundcloud.search(search_term=term)
            if isinstance(infos, dict):
                return json.dumps(infos)
            raise Exception(infos)

    def _add_discord_routes(self) -> None:
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


if __name__ == "__main__":
    NODE = Node()
    asyncio.get_event_loop().create_task(NODE.login())

    asyncio.get_event_loop().run_forever()
