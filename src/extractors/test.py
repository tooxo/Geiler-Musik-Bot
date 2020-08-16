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

    def test_genius_extract(self):
        ret1, ret2 = asyncio.run(
            Genius.extract_from_genius(
                "https://genius.com/Doja-cat-say-so-lyrics"
            )
        )

        self.assertEqual(
            ret1,
            "[Chorus]\nDay to night to morning, keep with me in the "
            "moment\nI'd let you had I known it, why don't you say "
            "so?\nDidn't even notice, no punches left to roll with\nYou got "
            "to keep me focused; you want it? Say so\nDay to night to "
            "morning, keep with me in the moment\nI'd let you had I known it, "
            "why don't you say so?\nDidn't even notice, no punches left to "
            "roll with\nYou got to keep me focused; you want it? Say so\n["
            "Verse 1]\nIt's been a long time since you fell in love\nYou "
            "ain't coming out your shell, you ain't really been "
            "yourself\nTell me, what must I do? (Do tell, my love)\n'Cause "
            "luckily I'm good at reading\nI wouldn't bug him, but he won't "
            "stop cheesin'\nAnd we can dance all day around it\nIf you "
            "frontin', I'll be bouncing\nIf you want it, scream it, shout it, "
            "babe\nBefore I leave you dry\n[Chorus]\nDay to night to morning, "
            "keep with me in the moment\nI'd let you had I known it, "
            "why don't you say so?\nDidn't even notice, no punches left to "
            "roll with\nYou got to keep me focused; you want it? Say so\nDay "
            "to night to morning, keep with me in the moment\nI'd let you had "
            "I known it, why don't you say so?\nDidn't even notice, "
            "no punches left to roll with\nYou got to keep me focused; you "
            "want it? Say so (Yeah)\n[Verse 2]\nLet me check my chest, "
            "my breath right quick (Ha)\nHe ain't ever seen it in a dress "
            "like this (Ah)\nHe ain't ever even been impressed like "
            "this\nProlly why I got him quiet on the set like zip\nLike it, "
            "love it, need it, bad\nTake it, own it, steal it, fast\nBoy, "
            "stop playing, grab my ass\nWhy you actin' like you shy? ("
            "Hot)\nShut it, save it, keep it pushin'\nWhy you beating 'round "
            "the bush?\nKnowin' you want all this woman\nNever knock it 'til "
            "you try (Yah, yah)\nAll of them bitches hating I have you with "
            "me\nAll of my niggas sayin' you mad committed\nRealer than "
            "anybody you had, and pretty\nAll of the body-ody, the ass and "
            "titties\n[Chorus]\nDay to night to morning, keep with me in the "
            "moment\nI'd let you had I known it, why don't you say "
            "so?\nDidn't even notice, no punches left to roll with\nYou got "
            "to keep me focused; you want it? Say so\nDay to night to "
            "morning, keep with me in the moment\nI'd let you had I known it, "
            "why don't you say so?\nDidn't even notice, no punches left to "
            "roll with\nYou got to keep me focused; you want it? Say so",
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
