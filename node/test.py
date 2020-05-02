# pylint: skip-file
import unittest

import av_audio_source


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


if __name__ == "__main__":
    unittest.main()
