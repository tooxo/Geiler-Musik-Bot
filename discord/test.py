# -*- coding: utf-8 -*-

"""
Used to test the used regex patterns.
"""

import unittest
import re
from url_parser import SpotifyType
from variable_store import VariableStore, strip_youtube_title


class Test(unittest.TestCase):
    """
    Runs the tests
    """

    spotify_urls = [
        ("https://www.google.com", False),
        (
            "http://open.spotify.com/user/tootallnate/playlist/0Lt5S4hGarhtZmtz7BNTeX",
            True,
        ),
        (
            "https://open.spotify.com/playlist/2ZKAnbi8ZG7mmiI0dJKrOg?si=jRVkuCJUREeljEOqUBqpLQ",
            True,
        ),
        (
            "https://open.spotify.com/playl ist/2ZKAnbi8ZG7mmiI0dJKrOg?si=jRVkuCJUREeljEOqUBqpLQ",
            False,
        ),
        (
            "https://open.spotify.com/track/384TqRlwlMfeUAODhXfF3O?si=PvtDF281TjWX0f6YvkhXOg",
            True,
        ),
        (
            "https://open.spotify.com/track/60eOMEt3WNVX1m1jmApmnX?si=6CP45EzJTGyBkKLRmhHmfw",
            True,
        ),
        (
            "https://open.spotify.com/album/4VzzEviJGYUtAeSsJlI9QB?si=hGIGlO4KSSyt8eO-QJ2VIw",
            True,
        ),
        (
            "https://open.spotify.com/artist/4kI8Ie27vjvonwaB2ePh8T?si=jyC9eGIiQbupvk0E2EE-vA",
            True,
        ),
        (
            "https://open.spotify.com/artist/4kI8Ie27v%vonwaB2ePh8T?si=jyC9eGIiQbupvk0E2EE-vA",
            False,
        ),
        (
            "https://open.spotify.com/artist/4kI8Ie27vjvonwaB2ePh8T?si=jyC9eGIiQbupvk0E2EE-vAa",
            False,
        ),
        ("https://oe.spotify.co/artist/JOSADJ98erwjoiasdoisjd(§sadjsdoi", False),
        (
            "https://open.spotify.com/artist/4kI8Ie27vjvonwaB2ePh8T?si=IVfCdRMFSauVtOIN9gEPnA",
            True,
        ),
        ("spotify:track:6QgjcU0zLnzq5OrUoSZ3OKa", False),
        ("spotify:track:6QgjcU0zLnzq5OrUoSZ3OK", True),
        ("spotify:ticktack:6QgjcU0zLnzq5OrUoSZ3OK", False),
        ("aspotifys:track:6QgjcU0zLnzq5OrUoSZ3OK", False),
    ]

    youtube_urls = [
        ("https://youtube.com", False),
        ("https://www.youtube.com/watch?v=0", False),
        ("https://www.youtube.com/watch?v=zrFI2gJSuwA", True),
        ("https://www.youtube.com/watch?test=12&v=zrFI2gJSuwA", True),
        ("https://www.youtube.com/watch?v=zrFI2gJSuA", False),
        (
            "https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj",
            True,
        ),
        (
            "https://www.youtube.com/plablist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj",
            False,
        ),
        (
            "ahttps://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxojo",
            False,
        ),
        (
            "https://www.youtube.com/playlist?list=PLMC9KNk       IncKtPzgY-5rmhvj7fax8fdxoj",
            False,
        ),
        ("https://youtu.be/k2qgadSvNyU", True),
        ("https://youtu.be/k2qgadyU", False),
        ("https://youtu.be/k2qgadSvNy U", False),
        ("https://youtu.be/k2qgadSvNy U?was=1", False),
        ("https://youtu.be/k2qgadSvNyU?was=1", True),
        ("http://youtu.be/k2qgadSvNyU?was=1", True),
        ("startstarthttps://www.youtube.com/watch?v=zrFI2gJSuwAendend", False),
    ]

    youtube_titles = [
        (
            "Ariana Grande - One Last Time (Lyric Video)",
            "Ariana Grande - One Last Time",
        ),
        (
            "Maroon 5 - Girls Like You (Lyrics) ft. Cardi B",
            "Maroon 5 - Girls Like You ft. Cardi B",
        ),
        ("bad guy - Billie Eilish (Lyrics)", "bad guy - Billie Eilish"),
        (
            "Shawn Mendes, Camila Cabello - Señorita (Lyrics)",
            "Shawn Mendes, Camila Cabello - Señorita",
        ),
        (
            "benny blanco, Juice WRLD - Graduation (Official Music Video)",
            "benny blanco, Juice WRLD - Graduation",
        ),
        ("Madcon - Beggin", "Madcon - Beggin"),
        (
            "Arctic Monkeys - Do I Wanna Know? (Official Video)",
            "Arctic Monkeys - Do I Wanna Know?",
        ),
        (
            "Daddy Yankee & Snow - Con Calma (Video Oficial)",
            "Daddy Yankee & Snow - Con Calma",
        ),
        (
            "Bruno Mars - Finesse (Remix) (feat. Cardi B] [Official Video]",
            "Bruno Mars - Finesse (Remix) (feat. Cardi B]",
        ),
    ]

    extract_urls = [
        (
            "https://www.youtube.com/watch?v=TJqL-UHQuP8&list=PLWdX866kdHceiAYM-lO_3AoVohzI3_8OD&index=5",
            "TJqL-UHQuP8",
        ),
        ("https://www.youtube.com/watch?v=1lWJXDG2i0A", "1lWJXDG2i0A"),
    ]

    def test_spotify_pattern(self):
        """
        Tests the Spotify Patterns with different Spotify URLS
        """
        for url, expected in Test.spotify_urls:
            if (
                re.match(VariableStore.spotify_url_pattern, url) is not None
                or re.match(VariableStore.spotify_uri_pattern, url) is not None
            ):
                self.assertEqual(expected, True)
            else:
                self.assertEqual(expected, False)
            self.assertEqual(SpotifyType(url).valid, expected)

    def test_youtube_pattern(self):
        """
        Tests the Youtube URL pattern with different urls
        """
        for url, expected in Test.youtube_urls:
            if re.match(VariableStore.youtube_video_pattern, url) is not None:
                self.assertEqual(expected, True)
            else:
                self.assertEqual(expected, False)

    def test_youtube_id_extract(self):
        """

        :return:
        """
        for url, _id in Test.extract_urls:
            self.assertEqual(VariableStore.youtube_url_to_id(url), _id)

    def test_strip_title(self):
        """
        Tests the Title Strip RegEX
        :return:
        """
        for title, expected in Test.youtube_titles:
            stripped = strip_youtube_title(title)
            self.assertEqual(expected, stripped)


if __name__ == "__main__":
    unittest.main()
