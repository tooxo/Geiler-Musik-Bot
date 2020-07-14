# pylint: skip-file

import asyncio
import functools
import time
import unittest

from bot.type.exceptions import (
    BasicError,
    NoResultsFound,
    PlaylistExtractionException,
)
from extractors.genius import Genius
from extractors.spotify import Spotify
from extractors.watch2gether import Watch2Gether


class ExtractorTest(unittest.TestCase):
    def tearDown(self) -> None:
        time.sleep(1)

    def test_genius_search(self):
        self.assertEqual(
            asyncio.run(Genius.search_genius("Take Care Drake", "")),
            "https://genius.com/Drake-take-care-lyrics",
        )
        self.assertEqual(
            asyncio.run(Genius.search_genius("Future Nostalgia", "")),
            "https://genius.com/Dua-lipa-future-nostalgia-lyrics",
        )
        f = functools.partial(
            asyncio.run,
            (
                Genius.search_genius(
                    "https://genius.com/api/search/multi?q=%3Cimg%20"
                    "src=x%20onerror=\x11%22javascript:alert(1)%22%3E",
                    "",
                )
            ),
        )
        self.assertRaises(
            NoResultsFound, f,
        )

    def __test_genius_extract__(self):
        # TODO: Not working, currently deactivated
        ret1, ret2 = asyncio.run(
            Genius.extract_from_genius(
                "https://genius.com/Doja-cat-say-so-lyrics"
            )
        )

        self.maxDiff = None

        self.assertEqual(
            ret1,
            "[Chorus]Day to night to morning, keep with me in the momen"
            "tI'd let you had I known it, why don't you say so"
            "?Didn't even notice, no\u2005punches left to roll withYou got "
            "to keep me focused; you want it? Say soDay to night to morning, "
            "keep with me in the momentI'd let you had I known it, why don't "
            "you say so?Didn't even notice, no punches left to roll withYou"
            " got to keep me focused; you want it? Say so[Verse 1]It's be"
            "en a long time since you fell in loveYou ain't coming out your s"
            "hell, you ain't really been yourselfTell me, what must I do? (Do"
            " tell, my love)'Cause luckily I'm good at readingI wouldn't bu"
            "g him, but he won't stop cheesin'And we can dance all day around"
            " itIf you frontin', I'll be bouncingIf you want it, scream it,"
            " shout it, babeBefore I leave you dry[Chorus]Day to night "
            "to morning, keep with me in the momentI'd let you had I known it"
            ", why don't you say so?Didn't even notice, no punches left to ro"
            "ll withYou got to keep me focused; you want it? Say soDay to n"
            "ight to morning, keep with me in the momentI'd let you had I kno"
            "wn it, why don't you say so?Didn't even notice, no punches left "
            "to roll withYou got to keep me focused; you want it? Say so (Yea"
            "h)[Verse 2]Let me check my chest, my breath right quick (Ha)"
            "He ain't ever seen it in a dress like this (Ah)He ain't ever e"
            "ven been impressed like thisProlly why I got him quiet on the se"
            "t like zipLike it, love it, need it, badTake it, own it, steal"
            " it, fastBoy, stop playing, grab my assWhy you actin' like you"
            " shy? (Hot)Shut it, save it, keep it pushin'Why you beating 'r"
            "ound the bush?Knowin' you want all this womanNever knock it 't"
            "il you try (Yah, yah)All of them bitches hating I have you with "
            "meAll of my niggas sayin' you mad committedRealer than anybody"
            " you had, and prettyAll of the body-ody, the ass and titties"
            "[Chorus]Day to night to morning, keep with me in the momentI'd"
            " let you had I known it, why don't you say so?Didn't even notice"
            ", no punches left to roll withYou got to keep me focused; you wa"
            "nt it? Say soDay to night to morning, keep with me in the moment"
            "I'd let you had I known it, why don't you say so?Didn't even n"
            "otice, no punches left to roll withYou got to keep me focused; y"
            "ou want it? Say so",
        )
        self.assertEqual(ret2, "Doja Cat - Say So")

        n = functools.partial(
            asyncio.run,
            (Genius.extract_from_genius("https://genius.com/Doja-cat-say-so-")),
        )

        self.assertRaises(BasicError, n)

    def test_watch2gether(self):
        loop = asyncio.new_event_loop()
        w = Watch2Gether(loop=loop)
        self.assertRegex(
            loop.run_until_complete(w.create_new_room()),
            r"https://www\.watch2gether\.com/rooms/\S{18}",
        )
        loop.run_until_complete(w.close())
        loop.close()

    def test_spotify_track(self):
        loop = asyncio.new_event_loop()
        s = Spotify(loop=loop)
        self.assertEqual(
            str(
                loop.run_until_complete(
                    s.spotify_track(
                        "https://open.spotify.com/track/34x6hEJgGAOQvmlMql5Ige?"
                        "si=TehGOt-iQlmxdG9HZj9ClA"
                    )
                )
            ),
            '{"title": "Kenny Loggins - Danger Zone - From \\"Top Gun\\" Origin'
            'al Soundtrack", "image_url": "https://i.scdn.co/image/ab67616d0000'
            'b27319db9ac54c80a898a179f0f1", "song_name": "Danger Zone - From \\'
            '"Top Gun\\" Original Soundtrack", "artist": "Kenny Loggins"}',
        )
        loop.run_until_complete(s.close())
        loop.close()

    def test_spotify_play(self):
        loop = asyncio.new_event_loop()
        s = Spotify(loop=loop)
        self.assertEqual(
            len(
                loop.run_until_complete(
                    s.spotify_playlist(
                        "https://open.spotify.com/playlist/37i9dQZEVXbMDoHDwVN2"
                        "tF?si=H7ICRUPhRNC250wJFLWyNw"
                    )
                )
            ),
            50,
        )
        self.assertEqual(
            len(
                loop.run_until_complete(
                    s.spotify_playlist(
                        "https://open.spotify.com/playlist/5NOIhb4nrzrw15skiTKY"
                        "EF?si=V7lRYLRcRN-HtQqy148Tew"
                    )
                )
            ),
            197,
        )
        self.assertRaises(
            PlaylistExtractionException,
            functools.partial(
                loop.run_until_complete,
                (
                    s.spotify_playlist(
                        "https://open.spotify.com/playlist/5NOIhb4nrzrw15skiTKY"
                        "I_AM_INVALID_EF"
                    )
                ),
            ),
        )
        self.assertRaises(
            PlaylistExtractionException,
            functools.partial(
                loop.run_until_complete,
                (
                    s.spotify_playlist(
                        "https://open.spotify.com/playlist/5NOIhb4nrzrw15skiTKY"
                        "EL"
                    )
                ),
            ),
        )
        self.assertEqual(
            len(
                loop.run_until_complete(
                    s.spotify_playlist(
                        "https://open.spotify.com/playlist/"
                        "4pKvDcT39olvUXtyaSN9IK?si=DC_BYOVsSf6RJlJS8q4C1A"
                    )
                )
            ),
            105,
        )
        self.assertRaises(
            PlaylistExtractionException,
            functools.partial(
                loop.run_until_complete,
                (
                    s.spotify_playlist(
                        "https://open.spotify.com/playlist/0RGyrEFFAnUKILU62SPn"
                        "3l"
                    )
                ),
            ),
        )
        loop.run_until_complete(s.close())
        loop.close()

    def test_spotify_album(self):
        loop = asyncio.new_event_loop()
        s = Spotify(loop=loop)
        self.assertEqual(
            len(
                loop.run_until_complete(
                    s.spotify_album(
                        "https://open.spotify.com/album/5fLOHW1UXr1cJrnXiU3FBt"
                        "?si=1V104dJ2Qg6WItr6eSRFzw"
                    )
                )
            ),
            10,
        )
        loop.run_until_complete(s.close())
        loop.close()

    def test_spotify_artist(self):
        loop = asyncio.new_event_loop()
        s = Spotify(loop=loop)
        self.assertEqual(
            len(
                loop.run_until_complete(
                    s.spotify_artist(
                        "https://open.spotify.com/artist/0LcJLqbBmaGUft1e9Mm8HV"
                        "?si=mrWCRRySTYeKp-wq-_xTsA"
                    )
                )
            ),
            10,
        )
        loop.run_until_complete(s.close())
        loop.close()


if __name__ == "__main__":
    unittest.main(warnings="ignore")
