# -*- coding: utf-8 -*-

import re
import unittest


def strip_youtube_title(title):
    title = re.sub(VariableStore.youtube_title_pattern, '', title)
    title = re.sub(VariableStore.space_cut_pattern, '', title)
    while "  " in title:
        title = title.replace("  ", " ")
    return title


class VariableStore:
    spotify_url_pattern = re.compile(
        r".*open\.spotify\.com/playlist.*|"
        r".*open\.spotify\.com/track.*|"
        r".*open\.spotify\.com/album.*|"
        r".*open\.spotify\.com/artist.*",
        re.IGNORECASE,
    )

    youtube_verify_pattern = re.compile(r"watch\?v=([a-zA-Z0-9]*)")

    youtube_url_pattern = re.compile(
        r".*youtube.com/watch\?.*v=[A-Za-z0-9]{11}(&.*)?|"
        r".*youtube.com/playlist\?[\S]*list=[\S]{34}|"
        r"(http(s)?://)?youtu\.be/[A-Za-z0-9]{11}", re.IGNORECASE | re.MULTILINE
    )

    url_pattern = re.compile(
        r"^(?:http(s)?://)?[\w.-]+(?:\.[\w.-]+)+[\w\-._~:/?#[\]@!$&'()*+,;=.]+$", re.IGNORECASE
    )

    youtube_title_pattern = re.compile(
        r"lyrics|\(lyrics\)|\[lyrics\]|"
        r"official lyric(s)? video|"
        r"\(official lyric(s)? video\)|\[official lyric(s)? video\]|"
        r"lyric(s)? video|"
        r"\(lyric(s)? video\)|"
        r"\[lyric(s)? video\]|"
        r"official video|official music video|"
        r"\[official video\]|\(official video\)|"
        r"\[official music video\]|\(official music video\)"
        , re.IGNORECASE
    )

    space_cut_pattern = re.compile(
        r"\s*$|^\s*",
        re.IGNORECASE
    )


class Test(unittest.TestCase):
    spotify_urls = [
        ("https://www.google.com", False),
        ("https://open.spotify.com/playlist/2ZKAnbi8ZG7mmiI0dJKrOg?si=jRVkuCJUREeljEOqUBqpLQ", True),
        ("https://open.spotify.com/playl ist/2ZKAnbi8ZG7mmiI0dJKrOg?si=jRVkuCJUREeljEOqUBqpLQ", False),
        ("https://open.spotify.com/track/384TqRlwlMfeUAODhXfF3O?si=PvtDF281TjWX0f6YvkhXOg", True),
        ("https://open.spotify.com/album/4VzzEviJGYUtAeSsJlI9QB?si=hGIGlO4KSSyt8eO-QJ2VIw", True),
        ("https://open.spotify.com/artist/4kI8Ie27vjvonwaB2ePh8T?si=jyC9eGIiQbupvk0E2EE-vA", True),
        ("https://oe.spotify.co/artist/JOSADJ98erwjoiasdoisjd(§sadjsdoi", False)
    ]

    youtube_urls = [
        ("https://youtube.com", False),
        ("https://www.youtube.com/watch?v=0", False),
        ("https://www.youtube.com/watch?v=zrFI2gJSuwA", True),
        ("https://www.youtube.com/watch?v=zrFI2gJSuA", False),
        ("https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj", True),
        ("https://www.youtube.com/plablist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj", False),
        ("https://www.youtube.com/playlist?list=PLMC9KNk       IncKtPzgY-5rmhvj7fax8fdxoj", False),
        ("https://youtu.be/k2qgadSvNyU", True),
        ("https://youtu.be/k2qgadyU", False),
        ("https://youtu.be/k2qgadSvNy U", False)
    ]

    youtube_titles = [
        ("Ariana Grande - One Last Time (Lyric Video)", "Ariana Grande - One Last Time"),
        ("Maroon 5 - Girls Like You (Lyrics) ft. Cardi B", "Maroon 5 - Girls Like You ft. Cardi B"),
        ("bad guy - Billie Eilish (Lyrics)", "bad guy - Billie Eilish"),
        ("Shawn Mendes, Camila Cabello - Señorita (Lyrics)", "Shawn Mendes, Camila Cabello - Señorita"),
        ("benny blanco, Juice WRLD - Graduation (Official Music Video)", "benny blanco, Juice WRLD - Graduation"),
        ("Madcon - Beggin", "Madcon - Beggin"),
        ("Arctic Monkeys - Do I Wanna Know? (Official Video)", "Arctic Monkeys - Do I Wanna Know?")
    ]

    def test_spotify_pattern(self):
        """
        Tests the Spotify Patterns with different Spotify URLS
        """
        for url, expected in Test.spotify_urls:
            if re.match(VariableStore.spotify_url_pattern, url) is not None:
                self.assertEqual(expected, True)
            else:
                self.assertEqual(expected, False)

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


if __name__ is '__main__':
    unittest.main()
