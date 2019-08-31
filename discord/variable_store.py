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

    spotify_uri_pattern = re.compile(r"^spotify:(track|playlist|album|artist):(?P<id>[A-Za-z0-9]{22})$", re.IGNORECASE)

    youtube_verify_pattern = re.compile(r"watch\?v=([a-zA-Z0-9]*)")
    #
    # youtube_url_pattern = re.compile(
    #     r"^(http(s)?://)?(www.)?youtube.com/watch\?(\S*&)?v=[A-Za-z0-9]{11}($|&)(\S*)?|"
    #     r"^(http(s)?://)?(www.)?youtube.com/playlist\?([\S]*&)?list=[\S]{34}($|&)\S*|"
    #     r"^(http(s)?://)?youtu\.be/[A-Za-z0-9]{11}($|\?)\S*",
    #     re.IGNORECASE,
    # )

    youtube_video_pattern = re.compile(
        r"^(http(s)?://)?(www.)?"
        r"(youtube.com/|youtu.be/)(watch|playlist)?\??([\S]*&)?(list=|v=)?"
        r"(?P<id>[\S]{11}|[\S]{34})($|&|\?)\S*",
        re.IGNORECASE,
    )

    url_pattern = re.compile(r"^(?:http(s)?://)?[\w.-]+(?:\.[\w.-]+)+[\w\-._~:/?#[\]@!$&'()*+,;=]+$", re.IGNORECASE)

    youtube_title_pattern = re.compile(
        r"[\[(]?"
        r"((official )?lyric(s)?( video)?|of(f)?icial (music )?video|video oficial|[2|4]K|(FULL[ |-]?)?HD)"
        r"[\])]?",
        re.IGNORECASE,
    )

    space_cut_pattern = re.compile(r"\s*$|^\s*", re.IGNORECASE)
