"""
FFmpegPCMAudio
"""
import audioop

from discord import FFmpegPCMAudio
from discord.opus import Encoder as OpusEncoder


# used for non opus
class FFmpegPCMAudioB(FFmpegPCMAudio):
    """
    FFmpegPCMAudioB
    """

    def __init__(self, source, volume, before_options) -> None:
        super().__init__(source=source, before_options=before_options)
        self.bytes_read = 0
        self.volume = volume

    def read(self) -> bytes:
        """
        Reads 20 ms of audio
        :return:
        """
        ret = self._stdout.read(OpusEncoder.FRAME_SIZE)
        if len(ret) != OpusEncoder.FRAME_SIZE:
            return b""
        self.bytes_read += OpusEncoder.FRAME_SIZE
        if self.volume != 1:
            ret = audioop.mul(ret, 2, self.volume)
        return ret

    def set_volume(self, volume: float) -> None:
        """
        Sets volume
        :param volume:
        :return:
        """
        self.volume = volume
