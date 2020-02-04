import audioop

import opuslib

from discord import FFmpegOpusAudio, FFmpegPCMAudio, PCMVolumeTransformer
from discord.opus import Encoder as OpusEncoder


# also used in soundcloud only
class FFmpegPCMAudioB(FFmpegPCMAudio):
    def __init__(self, source, *args, **kwargs):
        super().__init__(source, *args, **kwargs)
        self.bytes_read = 0

    def read(self):
        ret = self._stdout.read(OpusEncoder.FRAME_SIZE)
        if len(ret) != OpusEncoder.FRAME_SIZE:
            return b""
        self.bytes_read += OpusEncoder.FRAME_SIZE
        return ret


class FFmpegOpusAudioB(FFmpegOpusAudio):
    def __init__(self, source: str, volume=0.5, *args, **kwargs):
        self.volume = volume
        super().__init__(source, *args, **kwargs)
        self.bytes_read = 0

        self.decoder = opuslib.Decoder(
            OpusEncoder.SAMPLING_RATE, OpusEncoder.CHANNELS
        )
        self.encoder = opuslib.Encoder(
            OpusEncoder.SAMPLING_RATE, OpusEncoder.CHANNELS, "voip"
        )

    def read(self):
        """
        read 20ms of sound into memory
        :return: sound
        """
        self.bytes_read += OpusEncoder.FRAME_SIZE
        chunk = next(self._packet_iter, b"")
        if chunk == b"":
            # without this, the music won't ever stop :o
            return chunk
        try:
            if self.volume != 1.0:
                # shitty solution, but there is no better way.
                # TBA: external volume support (on node)
                decoded = self.decoder.decode(
                    chunk, OpusEncoder.SAMPLES_PER_FRAME, False
                )
                decoded = audioop.mul(decoded, 1, self.volume)
                chunk = self.encoder.encode(
                    decoded, OpusEncoder.SAMPLES_PER_FRAME
                )
        except opuslib.OpusError:
            pass
        return chunk

    def set_volume(self, volume: float):
        self.volume = volume

    @classmethod
    async def from_probe(cls, source, *, method=None, **kwargs):
        executable = kwargs.get("executable")
        codec, bitrate = await cls.probe(
            source, method=method, executable=executable
        )
        return cls(source, bitrate=bitrate, codec=codec, **kwargs)


# only used in soundcloud atm
class PCMVolumeTransformerB(PCMVolumeTransformer):
    def __init__(self, original: FFmpegPCMAudioB, volume=1.0):
        """
        transforms pcm sound
        :param original: original source
        :param volume: volume to change to
        """
        super().__init__(original, volume)

    @property
    def bytes_read(self):
        """
        Returns the bytes already read
        :return: bytes read
        """
        if isinstance(self.original, FFmpegPCMAudioB):
            return self.original.bytes_read
        return 0

    def set_volume(self, volume: float):
        self.volume = volume
