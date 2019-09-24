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
        r"(?P<id>[A-Za-z0-9]{22})(\?|$)(si=.{22})?$",
        re.IGNORECASE,
    )

    spotify_uri_pattern = re.compile(
        r"^spotify:(track|playlist|album|artist):(?P<id>[A-Za-z0-9]{22})$",
        re.IGNORECASE,
    )

    youtube_verify_pattern = re.compile(r"watch\?v=([a-zA-Z0-9]*)")

    youtube_video_pattern = re.compile(
        r"^(http(s)?://)?(www.)?"
        r"(youtube.com/|youtu.be/)(watch|playlist)?\??([\S]*&)?(list=|v=)?"
        r"(?P<id>[\S]{11}|[\S]{34})($|&|\?)\S*",
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

    """
    youtube_title_pattern = re.compile(
        r"[\[(]?"
        r"(((official )?lyric(s)?( video)?|of(f)?icial (music )?video|video oficial|[24]K|(FULL[ -]?)?HD)|(MV)?)+"
        r"[\])]?",
        re.IGNORECASE,
    )
    """

    space_cut_pattern = re.compile(r"\s*$|^\s*", re.IGNORECASE)


class Errors:
    no_results_found = "No Results found."
    default = "An Error has occurred."
    info_check = "An Error has occurred while checking Info."
    spotify_pull = (
        "**There was an error pulling the Spotify Playlist, 0 Songs were added.**"
    )
    cant_reach_youtube = "Can't reach YouTube. Server Error on their side maybe?"
