# pylint: skip-file
import asyncio
import functools
import json
import unittest

import av_audio_source
from node import NotAvailableException, SoundCloud, YouTube


class NodeTest(unittest.TestCase):
    def test_buffer(self):
        buf = av_audio_source.Buffer()
        buf.write(b"\x01" * 20)
        self.assertEqual(buf.available, 20)
        self.assertEqual(buf.read(10), b"\x01" * 10)
        self.assertEqual(buf.available, 10)
        buf.flush()
        self.assertEqual(len(buf), 0)
        self.assertEqual(buf.free, True)
        self.assertEqual(buf.closed, False)
        buf.__del__()
        self.assertEqual(buf.closed, True)

    def test_decoder_vol1(self):
        source = av_audio_source.AvAudioSource(
            "https://dl.espressif.com/dl/audio/ff-16b-2c-44100hz.opus", 1
        )
        self.assertEqual(source.bytes_read, 0)
        self.assertEqual(len(source.read()), 19)
        self.assertEqual(source.volume, 1)
        source.cleanup()

    def test_decoder_non_opus(self):
        source = av_audio_source.AvAudioSource(
            "https://dl.espressif.com/dl/audio/ff-16b-2c-44100hz.mp3", 1
        )
        self.assertEqual(source.bytes_read, 0)
        self.assertEqual(len(source.read()), 19)
        self.assertEqual(source.volume, 1)
        source.cleanup()

    def test_decoder_vol_05(self):
        source = av_audio_source.AvAudioSource(
            "https://dl.espressif.com/dl/audio/ff-16b-2c-44100hz.opus", 0.5
        )
        self.assertEqual(source.bytes_read, 0)
        self.assertEqual(len(source.read()), 19)
        self.assertEqual(source.volume, 0.5)
        source.cleanup()

    def test_decoder_non_opus_vol_05(self):
        source = av_audio_source.AvAudioSource(
            "https://dl.espressif.com/dl/audio/ff-16b-2c-44100hz.mp3", 0.5
        )
        self.assertEqual(source.bytes_read, 0)
        self.assertEqual(len(source.read()), 19)
        self.assertEqual(source.volume, 0.5)
        source.cleanup()


class NodeYouTubeTest(unittest.TestCase):
    def test_youtube_search_basic(self):
        y = YouTube()
        self.assertEqual(
            asyncio.run(
                y.search(
                    input_json=json.dumps(
                        {"term": "Despacito Luis Fonsi", "service": "basic"}
                    )
                )
            ),
            "https://youtube.com/watch?v=kJQP7kiw5Fk",
        )
        # try again for cache
        self.assertEqual(
            asyncio.run(
                y.search(
                    input_json=json.dumps(
                        {"term": "Despacito Luis Fonsi", "service": "basic"}
                    )
                )
            ),
            "https://youtube.com/watch?v=kJQP7kiw5Fk",
        )
        self.assertRaises(
            NotAvailableException,
            functools.partial(
                asyncio.run,
                (
                    y.search(
                        input_json=json.dumps(
                            {
                                "term": "sadhoiahf289ur9dsfö.c",
                                "service": "basic",
                            }
                        )
                    )
                ),
            ),
        )

    def test_youtube_search_music(self):
        y = YouTube()
        self.assertEqual(
            asyncio.run(
                y.search(
                    input_json=json.dumps(
                        {"term": "Despacito Luis Fonsi", "service": "music"}
                    )
                )
            ),
            "https://youtube.com/watch?v=kJQP7kiw5Fk",
        )
        # try again for cache
        self.assertEqual(
            asyncio.run(
                y.search(
                    input_json=json.dumps(
                        {"term": "Despacito Luis Fonsi", "service": "music"}
                    )
                )
            ),
            "https://youtube.com/watch?v=kJQP7kiw5Fk",
        )
        self.assertRaises(
            NotAvailableException,
            functools.partial(
                asyncio.run,
                (
                    y.search(
                        input_json=json.dumps(
                            {
                                "term": "sadhoiahf289ur9dsfö.c",
                                "service": "music",
                            }
                        )
                    )
                ),
            ),
        )

    def test_youtube_extraction(self):
        y = YouTube()
        self.assertTrue(
            asyncio.run(
                y.youtube_extraction(
                    "kJQP7kiw5Fk", "https://youtube.com/watch?v=kJQP7kiw5Fk"
                )
            )["stream"]
        )
        self.assertRaises(
            NotAvailableException,
            functools.partial(
                asyncio.run,
                (
                    y.youtube_extraction(
                        "kJQP7kiw5Fl", "https://youtube.com/watch?v=kJkr7niw5Fl"
                    )
                ),
            ),
        )

    def test_playlist(self):
        y = YouTube()
        self.assertEqual(
            len(
                asyncio.run(
                    y.extract_playlist("PLw-VjHDlEOgtl4ldJJ8Arb2WeSlAyBkJS")
                )
            ),
            100,
        )
        self.assertEqual(
            len(
                asyncio.run(
                    y.extract_playlist("PLw-VjHDlEOgtlkkkJJ8Arb2WeSlAyBkJS")
                )
            ),
            0,
        )


class NodeSoundCloudTest(unittest.TestCase):
    def test_search(self):
        s = SoundCloud()
        self.assertTrue(asyncio.run(s.search("roddy ricch the box"))["stream"],)
        self.assertRaises(
            NotAvailableException,
            functools.partial(asyncio.run, (s.search("sadjaosdij20930329a"))),
        )

    def test_track(self):
        s = SoundCloud()
        self.assertEqual(
            asyncio.run(
                s.research_track("https://soundcloud.com/roddyricch/the-box")
            )["title"],
            "The Box",
        )
        self.assertRaises(
            NotAvailableException,
            functools.partial(
                asyncio.run,
                (s.research_track("https://soundcloud.com/roddyricch/the-lox")),
            ),
        )

    def test_playlist(self):
        s = SoundCloud()
        self.assertEqual(
            len(
                asyncio.run(
                    s.playlist(
                        "https://soundcloud.com/user-319085523/sets/charts"
                    )
                )
            ),
            271,
        )


if __name__ == "__main__":
    unittest.main()
