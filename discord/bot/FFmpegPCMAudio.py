from discord import FFmpegPCMAudio, PCMVolumeTransformer
from discord.opus import Encoder as OpusEncoder

# Switch to FFmpegOpusAudio, when 1.3 is released


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
