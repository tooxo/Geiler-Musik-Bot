from discord import FFmpegPCMAudio, PCMVolumeTransformer, FFmpegOpusAudio
from discord.opus import Encoder as OpusEncoder


# Switch to FFmpegOpusAudio, when 1.3 is released
# now 1.3 is released, FFmpegOpusAudio can be used


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
        # exception for soundcloud opus server
        if "/cf-hls-opus-media.sndcdn.com" not in source:
            source += "&volume=" + str(volume)
        super().__init__(source, *args, **kwargs)
        self.bytes_read = 0

    def read(self):
        self.bytes_read += OpusEncoder.FRAME_SIZE
        return next(self._packet_iter, b"")


# only used in soundcloud atm
class PCMVolumeTransformerB(PCMVolumeTransformer):
    def __init__(self, original: FFmpegPCMAudioB, volume=1.0):
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
