# -*- coding: utf-8 -*-

"""
Used to test the used regex patterns.
"""
import asyncio
import re
import unittest

# noinspection PyUnresolvedReferences
from bot.type.exceptions import *

from bot.type.spotify_type import SpotifyType
from bot.type.youtube_type import YouTubeType
from bot.type.variable_store import VariableStore, strip_youtube_title
from bot.type.url import Url
from bot.type.soundcloud_type import SoundCloudType
from bot.type.song import Song
from bot.type.queue import Queue
from bot.type.errors import Errors
from bot.type.guild import Guild


class Test(unittest.TestCase):
    """
    Runs the tests
    """

    spotify_urls = [
        ("https://www.google.com", False),
        (
            "http://open.spotify.com/user/tootallnate/playlist/"
            "0Lt5S4hGarhtZmtz7BNTeX",
            True,
        ),
        (
            "https://open.spotify.com/playlist/2ZKAnbi8ZG7mmiI0dJKrOg"
            "?si=jRVkuCJUREeljEOqUBqpLQ",
            True,
        ),
        (
            "https://open.spotify.com/playl ist/2ZKAnbi8ZG7mmiI0dJKrOg"
            "?si=jRVkuCJUREeljEOqUBqpLQ",
            False,
        ),
        (
            "https://open.spotify.com/track/384TqRlwlMfeUAODhXfF3O"
            "?si=PvtDF281TjWX0f6YvkhXOg",
            True,
        ),
        (
            "https://open.spotify.com/track/60eOMEt3WNVX1m1jmApmnX"
            "?si=6CP45EzJTGyBkKLRmhHmfw",
            True,
        ),
        (
            "https://open.spotify.com/album/4VzzEviJGYUtAeSsJlI9QB"
            "?si=hGIGlO4KSSyt8eO-QJ2VIw",
            True,
        ),
        (
            "https://open.spotify.com/artist/4kI8Ie27vjvonwaB2ePh8T"
            "?si=jyC9eGIiQbupvk0E2EE-vA",
            True,
        ),
        (
            "https://open.spotify.com/artist/4kI8Ie27v%vonwaB2ePh8T"
            "?si=jyC9eGIiQbupvk0E2EE-vA",
            False,
        ),
        (
            "https://open.spotify.com/artist/4kI8Ie27vjvonwaB2ePh8T"
            "?si=jyC9eGIiQbupvk0E2EE-vAa",
            True,
        ),
        (
            "https://oe.spotify.co/artist/JOSADJ98erwjoiasdoisjd(§sadjsdoi",
            False,
        ),
        (
            "https://open.spotify.com/artist/"
            "4kI8Ie27vjvonwaB2ePh8T?si=IVfCdRMFSauVtOIN9gEPnA",
            True,
        ),
        ("spotify:track:6QgjcU0zLnzq5OrUoSZ3OKa", False),
        ("spotify:track:6QgjcU0zLnzq5OrUoSZ3OK", True),
        ("spotify:ticktack:6QgjcU0zLnzq5OrUoSZ3OK", False),
        ("aspotifys:track:6QgjcU0zLnzq5OrUoSZ3OK", False),
        (
            "https://open.spotify.com/playlist/"
            "7EmgNt7woAMyHa1Y7rPR6k?si=5htvOsARRN2rN2zWUFPr7Q+",
            True,
        ),
    ]

    youtube_urls = [
        ("https://youtube.com", False),
        ("https://www.youtube.com/watch?v=0", False),
        ("https://www.youtube.com/watch?v=zrFI2gJSuwA", True),
        ("https://www.youtube.com/watch?test=12&v=zrFI2gJSuwA", True),
        ("https://www.youtube.com/watch?v=zrFI2gJSuA", False),
        (
            "https://www.youtube.com/playlist?"
            "list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj",
            True,
        ),
        (
            "https://www.youtube.com/plablist?"
            "list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj",
            False,
        ),
        (
            "ahttps://www.youtube.com/playlist?"
            "list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxojo",
            False,
        ),
        (
            "https://www.youtube.com/playlist?list=PLMC9KNk    "
            "   IncKtPzgY-5rmhvj7fax8fdxoj",
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
        (
            "The Neighbourhood - Sweater Weather (Official Music Video)",
            "The Neighbourhood - Sweater Weather",
        ),
    ]

    extract_urls = [
        (
            "https://www.youtube.com/watch?v=TJqL-UHQuP8&list="
            "PLWdX866kdHceiAYM-lO_3AoVohzI3_8OD&index=5TJqL-UHQuP8",
            "TJqL-UHQuP8",
        ),
        ("https://www.youtube.com/watch?v=1lWJXDG2i0A", "1lWJXDG2i0A"),
        ("https://de.wikipedia.org/wiki/Mutter_(Software)", None),
        ("Nj2U6rhnucI", "Nj2U6rhnucI"),
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

    def test_spotify_detect_type(self):
        """
        Tests the Spotify test type
        @return:
        """
        self.assertEqual(
            SpotifyType(
                url="https://open.spotify.com/track/0qi4b1l0eT3jpzeNHeFXDT"
                "?si=qVMwkN1ySXSw2KJ-Bo_MAQ",
            ).type,
            SpotifyType.SPOTIFY_URL,
        )
        self.assertEqual(
            SpotifyType(url="spotify:track:0qi4b1l0eT3jpzeNHeFXDT").type,
            SpotifyType.SPOTIFY_URI,
        )
        self.assertEqual(
            SpotifyType(url="https://www.youtube.com/watch?v=spzZHIPMd6Q").type,
            None,
        )

    def test_spotify_id_extraction(self):
        """
        Test Spotify ID Extraction
        @return:
        """
        self.assertEqual(
            SpotifyType(
                "https://open.spotify.com/track/6GyFP1nfCDB8lbD2bG0Hq9"
                "?si=o-6i8HRoSe6yftQmciVOvg"
            ).id,
            "6GyFP1nfCDB8lbD2bG0Hq9",
        )
        self.assertEqual(
            SpotifyType("spotify:track:6GyFP1nfCDB8lbD2bG0Hq9").id,
            "6GyFP1nfCDB8lbD2bG0Hq9",
        )
        self.assertEqual(
            SpotifyType(url="https://www.youtube.com/watch?v=spzZHIPMd6Q").id,
            None,
        )

    def test_determine_source(self):
        """
        Test the determine source function
        @return:
        """
        self.assertEqual(
            Url.determine_source(
                "https://open.spotify.com/track/3Vo4wInECJQuz9BIBMOu8i"
                "?si=ehXTiTawTSKECHMaOKeF_A"
            ),
            Url.spotify,
        )
        self.assertEqual(
            Url.determine_source("https://www.youtube.com/watch?v=spzZHIPMd6Q"),
            Url.youtube,
        )
        self.assertEqual(
            Url.determine_source("https://soundcloud.com/roddyricch/the-box"),
            Url.soundcloud,
        )
        self.assertEqual(
            Url.determine_source("Roddy Ricch - The box"), Url.other
        )

    def test_spotify_type(self):
        """
        Test the spotify type detection
        @return:
        """
        self.assertEqual(
            Url.determine_spotify_type(
                "https://open.spotify.com/track/0hKF8N8aflF1uDzEEnPr2j"
                "?si=4sDh4YQfSRmMqOS4ZEidhQ"
            ),
            Url.spotify_track,
        )
        self.assertEqual(
            Url.determine_spotify_type(
                "https://open.spotify.com/album/5mJYFwj51OpBqRSxZCBLTT?si"
                "=L8b2dv6IRFuLA5tuRLaeHw"
            ),
            Url.spotify_album,
        )
        self.assertEqual(
            Url.determine_spotify_type(
                "https://open.spotify.com/album/5mJYFwj51OpBqRSxZCBLTT?si"
                "=L8b2dv6IRFuLA5tuRLaeHw"
            ),
            Url.spotify_album,
        )
        self.assertEqual(
            Url.determine_spotify_type(
                "https://open.spotify.com/artist/5Jj4mqGYiplyowPLKkJLHt"
                "?si=_Ci2-YN8T2K-Z9Wvo_tMCQ"
            ),
            Url.spotify_artist,
        )
        self.assertEqual(
            Url.determine_spotify_type(
                "https://open.spotify.com/playlist/37i9dQZEVXbMDoHDwVN2tF"
                "?si=9G4YpeGWRTu_0apMZTwwXA"
            ),
            Url.spotify_playlist,
        )
        self.assertEqual(Url.determine_spotify_type("not a valid type"), None)

    def test_soundcloud_detection(self):
        """
        Detect Soundcloud detection
        @return:
        """
        self.assertEqual(
            Url.determine_soundcloud_type(
                "https://soundcloud.com/roddyricch/sets/"
                "please-excuse-me-for-being"
            ),
            Url.soundcloud_set,
        )
        self.assertEqual(
            Url.determine_soundcloud_type(
                "https://soundcloud.com/roddyricch/the-box"
            ),
            Url.soundcloud_track,
        )
        self.assertEqual(
            Url.determine_soundcloud_type(
                "https://de.wikipedia.org/wiki/"
                "High-bandwidth_Digital_Content_Protection"
            ),
            None,
        )

    def test_youtube_detection(self):
        """
        Test Youtube type detection
        @return:
        """
        self.assertEqual(
            Url.determine_youtube_type(
                "https://www.youtube.com/watch?v=spzZHIPMd6Q"
            ),
            Url.youtube_url,
        )
        self.assertEqual(
            Url.determine_youtube_type("https://youtu.be/spzZHIPMd6Q"),
            Url.youtube_url,
        )
        self.assertEqual(
            Url.determine_youtube_type(
                "https://www.youtube.com/playlist?"
                "list=PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG"
            ),
            Url.youtube_playlist,
        )
        self.assertEqual(Url.determine_youtube_type("Charts TOP 50"), None)

    def test_youtube_valid(self):
        self.assertEqual(
            YouTubeType(
                "https://www.youtube.com/watch?v=Nj2U6rhnucI&list="
                "PLx0sYbCqOb8TBPRdmBHs5Iftvv9TPboYG"
            ).valid,
            True,
        )
        self.assertEqual(
            YouTubeType("https://www.youtube.com/watch?v=Nj2U6rhnucI").valid,
            True,
        )
        self.assertEqual(
            YouTubeType("https://youtu.be/Nj2U6rhnucI").valid, True,
        )
        self.assertEqual(
            YouTubeType(
                "https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=886154"
            ).valid,
            False,
        )

    def test_soundcloud_valid(self):
        self.assertEqual(
            SoundCloudType("https://soundcloud.com/roddyricch/the-box").valid,
            True,
        )
        self.assertEqual(
            SoundCloudType(
                "https://soundcloud.com/roddyricch/sets/"
                "please-excuse-me-for-being"
            ).valid,
            True,
        )
        self.assertEqual(
            SoundCloudType("https://www.youtube.com/").valid, False
        )

    def test_song_copy(self):
        """
        Test Song Copy
        @return:
        """
        a = Song(title="Test1", image_url="fest1", duration=1)
        b = Song(image_url="kalb53")
        c = Song.copy_song(a, b)
        self.assertEqual(c.title, "Test1")
        self.assertEqual(c.image_url, "kalb53")
        self.assertEqual(c.duration, 1)

    def test_stringify(self):
        self.assertEqual(str(Song(title="test")), '{"title": "test"}')

    def test_image(self):
        self.assertEqual(Song(image_url="image").image, "image")
        self.assertEqual(
            Song(image_url="image", thumbnail="thumb").image, "image"
        )
        self.assertEqual(Song(thumbnail="thumb").image, "thumb")
        self.assertEqual(Song().image, None)

    def test_song_copy_b(self):
        a = Song(title="2", duration=10, artist="jeff")
        self.assertEqual(str(Song(a)), str(a))

    def test_song_from_dict(self):
        self.assertEqual(
            str(Song.from_dict({"title": "hello", "duration": 10})),
            str(Song(title="hello", duration=10)),
        )

    def test_queue(self):
        q = Queue()
        q.put_nowait("test")
        q.put_nowait("test2")
        self.assertEqual(
            asyncio.get_event_loop().run_until_complete(q.get()), "test",
        )
        self.assertEqual(
            asyncio.get_event_loop().run_until_complete(q.get()), "test2",
        )
        self.assertIn("test", q.back_queue)
        q.put_nowait("test4")
        self.assertEqual(q.qsize(), 1)
        self.assertEqual(q.get_last(), "test")
        q.clear()
        self.assertEqual(q.qsize(), 0)

    def test_errors(self):
        self.assertEqual(
            Errors.as_list(),
            [
                "No Results found.",
                "An Error has occurred.",
                "An Error has occurred while checking Info.",
                "There was an error pulling the Playlist, 0 Songs were added. "
                "This may be caused by the playlist being private or deleted.",
                "Can't reach YouTube. Server Error on their side maybe?",
                "This YouTube Url is invalid.",
                "The requested song is not available.",
                "error_please_retry",
                "Our backend seems to be down right now, try again in a few "
                "minutes.",
            ],
        )

    def test_guild(self):
        test_guild = Guild()
        self.assertEqual(test_guild.service, "basic")
        self.assertEqual(test_guild.toggle_announce(), False)
        self.assertEqual(test_guild.toggle_announce(), True)
        self.assertRegex(
            str(test_guild),
            r"{'voice_client': None, 'voice_channel': None, 'song_queue': "
            r"<Queue at \S{14} maxsize=0>, 'now_playing_message': None, "
            r"'now_playing': None, 'volume': 0.5, 'full': '█', 'empty': '░', "
            r"'search_service': 'basic', 'announce': True, 'queue_lock': False}"
        )


if __name__ == "__main__":
    unittest.main()
