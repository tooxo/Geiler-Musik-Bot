# -*- coding: utf-8 -*-

import re


def strip_youtube_title(title):
    title = re.sub(VariableStore.youtube_title_pattern, "", title)
    title = re.sub(VariableStore.space_cut_pattern, "", title)
    while "  " in title:
        title = title.replace("  ", " ")
    return title


class VariableStore:
    spotify_url_pattern = re.compile(
        r"^(http(s)?://)?"
        r"(open\.|play\.)"
        r"spotify\.com/(user/.{,32}/)?(playlist|track|album|artist)/"
        r"(?P<id>[A-Za-z0-9]{22})(\?|$)(si=.{22,23})?$",
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
        r"(((official )?lyric(s)?( video)?)|of(f)?icial (music )?video|video oficial|[24]K|((FULL[ -]?)HD)|(MV))"
        r"[\])]?)",
        re.MULTILINE | re.IGNORECASE,
    )

    watch_url_pattern = re.compile(r"^[\S]{11}$", re.IGNORECASE)

    """
    youtube_title_pattern = re.compile(
        r"[\[(]?"
        r"(((official )?lyric(s)?( video)?|of(f)?icial (music )?video|video oficial|[24]K|(FULL[ -]?)?HD)|(MV)?)+"
        r"[\])]?",
        re.IGNORECASE,
    )
    """

    space_cut_pattern = re.compile(r"\s*$|^\s*", re.IGNORECASE)

    @staticmethod
    def youtube_url_to_id(url):
        if VariableStore.watch_url_pattern.match(url) is not None:
            return url
        m = VariableStore.youtube_video_pattern.match(url)
        if m:
            if "id2" in m.groupdict() and m.groupdict()["id2"] is not None:
                return m.group("id2")
            return m.group("id")
        return None


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
