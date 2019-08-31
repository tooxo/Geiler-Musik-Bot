# -*- coding: utf-8 -*-

import re
import unittest


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
        re.IGNORECASE
    )

    spotify_uri_pattern = re.compile(
        r"^spotify:(track|playlist|album|artist):(?P<id>[A-Za-z0-9]{22})$",
        re.IGNORECASE
    )

    youtube_verify_pattern = re.compile(r"watch\?v=([a-zA-Z0-9]*)")

    youtube_url_pattern = re.compile(
        r"^(http(s)?://)?(www.)?youtube.com/watch\?(\S*&)?v=[A-Za-z0-9]{11}($|&)(\S*)?|"
        r"^(http(s)?://)?(www.)?youtube.com/playlist\?([\S]*&)?list=[\S]{34}($|&)\S*|"
        r"^(http(s)?://)?youtu\.be/[A-Za-z0-9]{11}($|\?)\S*",
        re.IGNORECASE,
    )

    url_pattern = re.compile(r"^(?:http(s)?://)?[\w.-]+(?:\.[\w.-]+)+[\w\-._~:/?#[\]@!$&'()*+,;=]+$", re.IGNORECASE)

    youtube_title_pattern = re.compile(
        r"[\[(]?"
        r"((official )?lyric(s)?( video)?|of(f)?icial (music )?video|video oficial|[2|4]K|(FULL[ |-]?)?HD)"
        r"[\])]?",
        re.IGNORECASE
    )

    space_cut_pattern = re.compile(r"\s*$|^\s*", re.IGNORECASE)


class Test(unittest.TestCase):
    spotify_urls = [
        ("https://www.google.com", False),
        ('http://open.spotify.com/user/tootallnate/playlist/0Lt5S4hGarhtZmtz7BNTeX', True),
        ("https://open.spotify.com/playlist/2ZKAnbi8ZG7mmiI0dJKrOg?si=jRVkuCJUREeljEOqUBqpLQ", True),
        ("https://open.spotify.com/playl ist/2ZKAnbi8ZG7mmiI0dJKrOg?si=jRVkuCJUREeljEOqUBqpLQ", False),
        ("https://open.spotify.com/track/384TqRlwlMfeUAODhXfF3O?si=PvtDF281TjWX0f6YvkhXOg", True),
        ("https://open.spotify.com/track/60eOMEt3WNVX1m1jmApmnX?si=6CP45EzJTGyBkKLRmhHmfw", True),
        ("https://open.spotify.com/album/4VzzEviJGYUtAeSsJlI9QB?si=hGIGlO4KSSyt8eO-QJ2VIw", True),
        ("https://open.spotify.com/artist/4kI8Ie27vjvonwaB2ePh8T?si=jyC9eGIiQbupvk0E2EE-vA", True),
        ("https://open.spotify.com/artist/4kI8Ie27vjvonwaB2ePh8T?si=jyC9eGIiQbupvk0E2EE-vAa", False),
        ("https://oe.spotify.co/artist/JOSADJ98erwjoiasdoisjd(§sadjsdoi", False),
        ("https://open.spotify.com/artist/4kI8Ie27vjvonwaB2ePh8T?si=IVfCdRMFSauVtOIN9gEPnA", True),
        ("spotify:track:6QgjcU0zLnzq5OrUoSZ3OKa", False),
        ("spotify:track:6QgjcU0zLnzq5OrUoSZ3OK", True),
        ("spotify:ticktack:6QgjcU0zLnzq5OrUoSZ3OK", False),
        ("aspotifys:track:6QgjcU0zLnzq5OrUoSZ3OK", False)
    ]

    youtube_urls = [
        ("https://youtube.com", False),
        ("https://www.youtube.com/watch?v=0", False),
        ("https://www.youtube.com/watch?v=zrFI2gJSuwA", True),
        ("https://www.youtube.com/watch?test=12&v=zrFI2gJSuwA", True),
        ("https://www.youtube.com/watch?v=zrFI2gJSuA", False),
        ("https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj", True),
        ("https://www.youtube.com/plablist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj", False),
        ("ahttps://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxojo", False),
        ("https://www.youtube.com/playlist?list=PLMC9KNk       IncKtPzgY-5rmhvj7fax8fdxoj", False),
        ("https://youtu.be/k2qgadSvNyU", True),
        ("https://youtu.be/k2qgadyU", False),
        ("https://youtu.be/k2qgadSvNy U", False),
        ("https://youtu.be/k2qgadSvNy U?was=1", False),
        ("https://youtu.be/k2qgadSvNyU?was=1", True),
        ("http://youtu.be/k2qgadSvNyU?was=1", True),
        ("startstarthttps://www.youtube.com/watch?v=zrFI2gJSuwAendend", False)
    ]

    youtube_titles = [
        ("Ariana Grande - One Last Time (Lyric Video)", "Ariana Grande - One Last Time"),
        ("Maroon 5 - Girls Like You (Lyrics) ft. Cardi B", "Maroon 5 - Girls Like You ft. Cardi B"),
        ("bad guy - Billie Eilish (Lyrics)", "bad guy - Billie Eilish"),
        ("Shawn Mendes, Camila Cabello - Señorita (Lyrics)", "Shawn Mendes, Camila Cabello - Señorita"),
        ("benny blanco, Juice WRLD - Graduation (Official Music Video)", "benny blanco, Juice WRLD - Graduation"),
        ("Madcon - Beggin", "Madcon - Beggin"),
        ("Arctic Monkeys - Do I Wanna Know? (Official Video)", "Arctic Monkeys - Do I Wanna Know?"),
        ("Daddy Yankee & Snow - Con Calma (Video Oficial)", "Daddy Yankee & Snow - Con Calma"),
    ]

    def test_spotify_pattern(self):
        """
        Tests the Spotify Patterns with different Spotify URLS
        """
        for url, expected in Test.spotify_urls:
            if re.match(VariableStore.spotify_url_pattern, url) is not None or re.match(
                    VariableStore.spotify_uri_pattern, url) is not None:
                self.assertEqual(expected, True)
            else:
                self.assertEqual(expected, False)
            self.assertEqual(SpotifyType(url).valid, expected)

    def test_youtube_pattern(self):
        """
        Tests the Youtube URL pattern with diffrent urls
        """
        for url, expected in Test.youtube_urls:
            if re.match(VariableStore.youtube_url_pattern, url) is not None:
                self.assertEqual(expected, True)
            else:
                self.assertEqual(expected, False)

    def test_strip_title(self):
        for title, expected in Test.youtube_titles:
            stripped = strip_youtube_title(title)
            self.assertEqual(expected, stripped)


if __name__ is "__main__":
    unittest.main()


class SpotifyType:
    def __init__(self, url):
        self.url = url
        self.URI = "SPOTIFY_URI"
        self.URL = "SPOTIFY_URL"

    @property
    def valid(self):
        if re.match(VariableStore.spotify_url_pattern, self.url) is not None:
            return True
        if re.match(VariableStore.spotify_uri_pattern, self.url) is not None:
            return True
        return False

    @property
    def type(self):
        if self.valid:
            if re.match(VariableStore.spotify_url_pattern, self.url) is not None:
                return self.URL
            if re.match(VariableStore.spotify_uri_pattern, self.url) is not None:
                return self.URI
        return None

    @property
    def id(self):
        if self.type is self.URL:
            return re.search(VariableStore.spotify_url_pattern, self.url).group("id")
        if self.type is self.URI:
            return re.search(VariableStore.spotify_uri_pattern, self.url).group("id")
        if self.type is None:
            return None
