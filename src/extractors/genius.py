"""
Genius
"""
import re
import traceback
import json
import urllib.parse
from typing import Tuple
from html import unescape

import aiohttp
import async_timeout

import logging_manager
from bot.type.errors import Errors
from bot.type.exceptions import BasicError, NoResultsFound

# pulled from my project ArtistWordRanker:
# https://github.com/tooxo/ArtistWordRanker


class Genius:
    """
    Genius
    """

    TITLE_PATTERN = re.compile(
        r"<h1[^>]*header_with_cover_art-primary_info-title[^>]*>(.+)</h1>", re.S
    )
    TITLE_PATTERN_2 = re.compile(
        r'<h1 class="SongHeader__Title-sc-1b7aqpg-7 \S+">([^<]+)</h1>', re.S
    )
    ARTIST_PATTERN = re.compile(
        r"<a[^>]*header_with_cover_art-primary_info-primary_artist"
        r"[^>]*>([^<]*)</a>",
        re.S,
    )
    ARTIST_PATTERN_2 = re.compile(
        r'<a[^>]+class="Link-h3isu4-0 dpVWpH '
        r'SongHeader__Artist-sc-1b7aqpg-8 \S+"[^>]+>([^<]+)</a>',
        re.S,
    )
    PRELOADED_STATE_PATTERN = re.compile(
        r"window\.__PRELOADED_STATE__ = JSON\.parse\('(.+)'\);", re.DOTALL
    )

    @staticmethod
    async def search_genius(track_name: str, artist: str):
        """
        Search Genius
        @param track_name:
        @param artist:
        @return:
        """
        base_url = "https://genius.com/api/search/song?q="
        url = base_url + urllib.parse.quote(
            re.sub(r"\(.+\)", string=track_name, repl="")
            + " "
            + re.sub(r"\(.+\)", string=artist, repl="")
        )
        async with async_timeout.timeout(timeout=8):
            async with aiohttp.request("GET", url=url) as resp:
                if resp.status not in (200, 301, 302):
                    raise BasicError(Errors.default)
                response = await resp.json()
                try:
                    for cat in response["response"]["sections"]:
                        for item in sorted(
                            cat["hits"],
                            key=lambda i: i["result"]["stats"].get(
                                "pageviews", 0
                            ),
                            reverse=True,
                        ):
                            if item["result"]["url"].endswith("lyrics"):
                                return item["result"]["url"]
                except (IndexError, ValueError, TypeError):
                    traceback.print_exc()
                raise NoResultsFound(Errors.no_results_found)

    @staticmethod
    async def extract_from_genius(url: str) -> Tuple[str, str]:
        """
        Extract lyrics from genius
        @param url:
        @return:
        """
        async with async_timeout.timeout(timeout=8):
            async with aiohttp.request("GET", url=url) as resp:
                if resp.status not in (200, 301, 302):
                    logging_manager.LoggingManager().info(
                        "Genius search failed with: " + url
                    )
                    resp.close()
                    raise BasicError(Errors.default)
                text = (await resp.read()).decode("UTF-8")
                if "LyricsPlaceholder__Message" in text:
                    parsed_lyrics = "This song is an instrumental"
                else:
                    if '<div class="lyrics">' in text:
                        raw_lyrics = text.split('<div class="lyrics">')[1]
                        raw_lyrics = raw_lyrics.split("<!--sse-->")[1]
                        raw_lyrics = raw_lyrics.split(" <!--/sse-->")[0]
                        parsed_lyrics = raw_lyrics
                    else:
                        raw_json = Genius.PRELOADED_STATE_PATTERN.search(
                            text
                        ).group(1)
                        if "');" in raw_json:
                            raw_json = raw_json.split("');")[0]
                        # raw_json = raw_json.encode("utf-8").decode(
                        #    "unicode-escape"
                        # )
                        raw_json = (
                            raw_json.replace('\\\\"', '\\"')
                            .replace('\\"', '"')
                            .replace("\\'", "")
                        )
                        if r"\$" in raw_json:
                            raw_json = raw_json.replace(r"\$", "")
                        raw_json = raw_json.replace("\u2005", " ")
                        js_obj = json.loads(raw_json)
                        parsed_lyrics = ""
                        for child in js_obj["songPage"]["lyricsData"]["body"][
                            "children"
                        ]:
                            if isinstance(child, str):
                                continue
                            for txt in child["children"]:
                                if isinstance(txt, dict):
                                    if len(txt.keys()) == 1:
                                        continue
                                    lyrics_list = []
                                    if "children" in txt:
                                        for proposed_lyric in txt["children"]:
                                            if isinstance(proposed_lyric, str):
                                                lyrics_list.append(
                                                    proposed_lyric
                                                )
                                            elif len(proposed_lyric.keys()) > 1:
                                                lyrics_list.extend(
                                                    proposed_lyric["children"]
                                                )
                                            else:
                                                lyrics_list.append("\n")
                                    else:
                                        lyrics_list.append("\n")
                                    parsed_lyrics += "".join(lyrics_list) + "\n"

                                else:
                                    parsed_lyrics += txt
                                    parsed_lyrics += "\n"

                artist_matcher = Genius.ARTIST_PATTERN.search(text)
                if not artist_matcher:
                    artist_matcher = Genius.ARTIST_PATTERN_2.search(text)
                artist = artist_matcher.group(1)
                title_matcher = Genius.TITLE_PATTERN.search(text)
                if not title_matcher:
                    title_matcher = Genius.TITLE_PATTERN_2.search(text)
                title = title_matcher.group(1)
            return (
                LyricsCleanup.clean_up(lyrics=parsed_lyrics),
                artist + " - " + title,
            )


class LyricsCleanup:
    """
    LyricsCleanup
    """

    @staticmethod
    def remove_html_tags(lyrics: str):
        """
        This removes any other html tags from the lyrics
        (the regex was stolen from here: https://www.regextester.com/93515)
        :param lyrics: input lyrics
        :return: filtered lyrics
        """
        html_tag_regex = r"<[^>]*>"
        return re.sub(pattern=html_tag_regex, string=lyrics, repl="")

    @staticmethod
    def remove_double_spaces(lyrics: str) -> str:
        """
        Remove double spaces from the lyrics
        @param lyrics:
        @return:
        """
        while "  " in lyrics:
            lyrics = lyrics.replace("  ", " ")
        return lyrics

    @staticmethod
    def remove_double_newlines(lyrics: str) -> str:
        """

        @param lyrics:
        @return:
        """
        while "\n\n" in lyrics:
            lyrics = lyrics.replace("\n\n", "\n")
        return lyrics

    @staticmethod
    def remove_start_and_end_spaces(lyrics: str) -> str:
        """
        Remove spaces at the start and the end of the lyrics
        @param lyrics:
        @return:
        """
        start_of_line = r"^[ ]+"
        end_of_line = r"[ ]+$"
        lyrics = re.sub(
            pattern=start_of_line, string=lyrics, repl="", flags=re.M
        )
        lyrics = re.sub(pattern=end_of_line, string=lyrics, repl="", flags=re.M)
        return lyrics

    @staticmethod
    def clean_up(lyrics: str) -> str:
        """
        runs all of them
        :param lyrics:
        :return:
        """
        return unescape(
            LyricsCleanup.remove_start_and_end_spaces(
                LyricsCleanup.remove_double_newlines(
                    LyricsCleanup.remove_double_spaces(
                        LyricsCleanup.remove_html_tags(lyrics=lyrics)
                    )
                )
            )
        ).strip()
