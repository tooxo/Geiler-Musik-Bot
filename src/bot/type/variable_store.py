"""
VariableStore
"""
# -*- coding: utf-8 -*-

import re


def strip_youtube_title(title: str) -> str:
    """
    Strip unnecessary information from YouTube titles
    @param title:
    @return:
    """
    title = re.sub(VariableStore.youtube_title_pattern, "", title)
    title = re.sub(VariableStore.space_cut_pattern, "", title)
    title = re.sub(VariableStore.empty_brackets_pattern, "", title)
    while "  " in title:
        title = title.replace("  ", " ")
    return title


class VariableStore:
    """
    VariableStore
    """

    spotify_url_pattern = re.compile(
        r"^(http(s)?://)?"
        r"(open\.|play\.)"
        r"spotify\.com/(user/.{,32}/)?(playlist|track|album|artist)/"
        r"(?P<id>[A-Za-z0-9]{22,23})(\?|$)(si=.{22,23})?$",
        re.IGNORECASE,
    )

    spotify_uri_pattern = re.compile(
        r"^spotify:(track|playlist|album|artist):(?P<id>[A-Za-z0-9]{22})$",
        re.IGNORECASE,
    )

    youtube_verify_pattern = re.compile(r"watch\?v=([a-zA-Z0-9]*)")

    youtube_video_pattern = re.compile(
        r"^(http(s)?://)?(www.)?(youtube.com/|youtu.be/)"
        r"(watch|playlist)?\??(v=(?P<id2>[\S]{11})&)?"
        r"([\S]*&)?(v=|list=)?(?P<id>[\S]{11}|[\S]{34})($|&|\?)\S*",
        re.IGNORECASE,
    )

    url_pattern = re.compile(
        r"^(?:http(s)?://)?[\w.-]+(?:\.[\w.-]+)+[\w\-._~:/?#[\]@!$&'()*+,;=]+$",
        re.IGNORECASE,
    )

    youtube_title_pattern = re.compile(
        r"([\[(]?"
        r"(((official )?lyric(s)?( video)?)|of(f)?icial (music )?video|"
        r"(of(f)?icial )?audio|"
        r"video oficial| [24]K|((FULL[ -]?)HD)|(MV))"
        r"[\])]?)",
        re.MULTILINE | re.IGNORECASE,
    )

    empty_brackets_pattern = re.compile(
        r"\([ ]+\)", re.MULTILINE | re.IGNORECASE
    )

    soundcloud_url_pattern = re.compile(
        r"https?://(?:w\.|www\.|)(?:soundcloud\.com/)(?:|)"
        r"(((\w|-)[^A-z]{7})|([A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*(?!"
        r"/sets(?:/|$))(?:/[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*){1,2}))",
        re.MULTILINE | re.IGNORECASE,
    )

    soundcloud_sets_pattern = re.compile(
        r"https?://(www\.)?soundcloud\.com"
        r"/([A-Za-z0-9_-]+)/([A-Za-z0-9_-]+)[^< ]*",
        re.MULTILINE | re.IGNORECASE,
    )

    watch_url_pattern = re.compile(r"^[\S]{11}$", re.IGNORECASE)

    space_cut_pattern = re.compile(r"\s*$|^\s*", re.IGNORECASE)

    @staticmethod
    def youtube_url_to_id(url):
        """
        Extract the Id from the YouTube url
        @param url:
        @return:
        """
        if VariableStore.watch_url_pattern.match(url) is not None:
            return url
        match = VariableStore.youtube_video_pattern.match(url)
        if match:
            if (
                "id2" in match.groupdict()
                and match.groupdict()["id2"] is not None
            ):
                return match.group("id2")
            return match.group("id")
        return None
